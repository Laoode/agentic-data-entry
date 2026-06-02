# RECIPE-DB: Pre-Fine-Tuning Dataset Pipeline
## RECeipt Image Processing & Extraction DataBase

**Tujuan:** Membangun dataset anotasi receipt untuk fine-tuning LoRA pada model GLM-OCR agar mampu mengekstrak Key Information Extraction (KIE) terstruktur dari gambar receipt secara langsung.

**Oxen Repository:** https://www.oxen.ai/Laoode/RECIPE-DB  
**Stack:** GLM-OCR (vLLM) · Gemini 3.1 Pro Preview · LLaMA-Factory · Label Studio · Oxen AI

---

## Daftar Isi

1. [Latar Belakang & Motivasi](#1-latar-belakang--motivasi)
2. [Arsitektur Sistem](#2-arsitektur-sistem)
3. [Fondasi Teoritis: KIE Paper](#3-fondasi-teoritis-kie-paper)
4. [Dataset & Distribusi](#4-dataset--distribusi)
5. [Schema Ekstraksi](#5-schema-ekstraksi)
6. [Perancangan Prompt Engineering](#6-perancangan-prompt-engineering)
7. [Pipeline Step-by-Step](#7-pipeline-step-by-step)
8. [Workflow End-to-End](#8-workflow-end-to-end)
9. [Struktur File & Direktori](#9-struktur-file--direktori)
10. [Konfigurasi Environment](#10-konfigurasi-environment)
11. [Rate Limiting & Budget Strategy](#11-rate-limiting--budget-strategy)
12. [Versioning Dataset dengan Oxen](#12-versioning-dataset-dengan-oxen)
13. [Fine-Tuning LoRA](#13-fine-tuning-lora)
14. [Design Decisions & Trade-offs](#14-design-decisions--trade-offs)

---

## 1. Latar Belakang & Motivasi

### Masalah

GLM-OCR out-of-the-box hanya menghasilkan plain text dari gambar dokumen. Untuk use case production — ekstraksi `store_name`, `grand_total`, `items`, `payment_method` — model perlu menghasilkan **JSON terstruktur langsung dari gambar**, tanpa pipeline Gemini di tengah.

### Solusi: Fine-Tuning dengan Data Sintetis

Kami membangun pipeline untuk membuat training data berkualitas tinggi:

```
Gambar Receipt
     ↓  GLM-OCR (OCR)         → teks mentah
     ↓  Gemini 3.1 Pro (KIE)  → JSON terstruktur
     ↓  Manual Review          → anotasi terverifikasi
     ↓  LLaMA-Factory Format   → dataset fine-tuning
     ↓  LoRA Fine-tuning       → GLM-OCR yang bisa langsung output JSON
```

### Arsitektur Dua-Model

Keputusan desain awal: **pisahkan persepsi dari reasoning**.

| Layer | Model | Fungsi |
|---|---|---|
| Perception | GLM-OCR (0.9B) | Baca gambar → teks; tidak reasoning |
| Reasoning | Supervisor Klaudia | Semantic reasoning; tidak lihat gambar |

Untuk training data, Gemini Pro menggantikan peran Supervisor untuk generate ground truth annotation.

---

## 2. Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────┐
│                    RECIPE-DB Pipeline                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  raw_data/                                              │
│  ├── cord-v2/images/train/    ─┐                        │
│  ├── e_receipt/images/        ─┤                        │
│  ├── expressexpense/images/   ─┤                        │
│  ├── nanonets/images/         ─┼─ SOURCE IMAGES         │
│  ├── roboflow/train/images/   ─┤                        │
│  ├── pinterest/images/        ─┤                        │
│  ├── sroie/train/img/         ─┤                        │
│  └── uniquedata/images/       ─┘                        │
│            │                                            │
│            ▼  1_ocr_extractor.py                        │
│            │  (GLM-OCR via vLLM, 24 concurrent)         │
│            ▼                                            │
│  LLaMA-Factory/data/recipe_db/                          │
│  ├── train/                                             │
│  │   ├── images/  *.jpg   ← converted + validated       │
│  │   ├── ocr/     *.txt   ← GLM-OCR raw text            │
│  │   └── labels/  *.json  ← (empty, filled by step 2)   │
│  └── test/                                              │
│      ├── images/                                        │
│      ├── ocr/                                           │
│      └── labels/                                        │
│            │                                            │
│            ▼  2_kie_processor.py                        │
│            │  (Gemini 3.1 Pro Preview, 240 RPD/day)      │
│            ▼                                            │
│  labels/  *.json  ← structured KIE output              │
│            │                                            │
│            ▼  3_label_studio_converter.py               │
│            │  (export + manual review + import)          │
│            ▼                                            │
│  labels/  *.json  ← verified & corrected                │
│            │                                            │
│            ▼  4_final_formatter.py                      │
│            │  (ShareGPT format for LLaMA-Factory)        │
│            ▼                                            │
│  LLaMA-Factory/data/                                    │
│  ├── recipe_db_train.json                               │
│  ├── recipe_db_test.json                                │
│  └── dataset_info.json                                  │
│            │                                            │
│            ▼  llamafactory-cli train                    │
│            │  (LoRA, rank 8, L4 24GB)                    │
│            ▼                                            │
│  GLM-OCR-LoRA (merged) → langsung output JSON          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Fondasi Teoritis: KIE Paper

Seluruh pendekatan prompt engineering mengacu pada paper:

> **"Evaluation of Prompt Engineering on the Performance of a Large Language Model in Document Information Extraction"**

Cite: 
> Chen, L.-C., Weng, H.-T., Mayuresh Sunil Pardeshi, Chen, C.-M., Sheu, R.-K. and Pai, K.-C. (2025). Evaluation of Prompt Engineering on the Performance of a Large Language Model in Document Information Extraction. Electronics, [online] 14(11), pp.2145–2145. doi:https://doi.org/10.3390/electronics14112145.

‌
### Pipeline yang Diadopsi dari Paper

Paper mendefinisikan pipeline KIE sebagai:

```
OCR Output → Configuration Module → LLM → Confidence Calculation
```

Kami mengadaptasinya menjadi:

```
GLM-OCR Text → config.py (schema + rules) → Gemini → JSON Validation
```

### Temuan Paper yang Diterapkan

#### 1. Manual Prompt dengan Field-Specific Rules (86.8% akurasi)
Pendekatan terbaik adalah memberikan instruksi spesifik per field, bukan instruksi umum.

**Contoh implementasi di `EXTRACTION_RULES`:**
```
store_contacts:
- Extract the label exactly as written into "type"
- If NO label exists, "type" MUST be ""
- DO NOT classify or guess

items:
- item_name: ONLY descriptive text, NO SKU/barcode
- quantity: number only, never "x", "@", "PCS"
```

#### 2. One-Shot Learning (50% peningkatan vs zero-shot)
Paper membuktikan satu contoh konkret secara signifikan meningkatkan akurasi vs prompt tanpa contoh.

**Implementasi:** `FEW_SHOT_RECEIPT_TEXT` + `FEW_SHOT_OUTPUT` — receipt buatan yang mendemonstrasikan semua edge case.

#### 3. Prompt Repetition (47 wins / 0 losses)
Dari paper "Prompt Repetition for Non-Reasoning Models": mengulang seluruh instruction block 2x meningkatkan akurasi NameIndex dari 21% → 97% pada Gemini Flash-Lite.

**Mekanisme:** Setiap token prompt dapat attend ke semua token lain (causal attention limitation workaround).

**Implementasi modular via `.env`:**
```properties
# Thinking models (Gemini 3.1 Pro Preview): DISABLE
# Reasoning sudah terjadi internally, repetition membuang token
PROMPT_REPETITION=false

# Non-thinking models (Gemini Flash, etc.): ENABLE
PROMPT_REPETITION=true
```

### Tabel Perbandingan Teknik dari Paper

| Teknik | Akurasi (paper) | Diterapkan |
|---|---|---|
| Zero-shot | Baseline | ✗ |
| Zero-shot + rules | ~72% | ✗ |
| Few-shot (1 example) | +50% vs zero-shot | ✓ |
| Manual prompt + rules | 86.8% | ✓ |
| APE (Auto Prompt Engineer) | Terbaik di beberapa field | Future work |
| Prompt Repetition | 47/70 wins, 0 losses | ✓ (modular) |

---

## 4. Dataset & Distribusi

### Sumber Data

| Dataset | Jumlah Total | Digunakan | Bahasa | Mata Uang |
|---|---|---|---|---|
| CORD-V2 | 999 | 50 | Indo, Eng | Rp |
| E-Receipt | 53 | 53 (full) | Indo, Eng | Rp, $ |
| Express Expense | 200 | 50 | Eng | € |
| Nanonets | 987 | 50 | Malay, Eng | RM |
| Roboflow | 1.746 | 50 | Indo, Malay, Eng | Rp, RM, €, $ |
| Pinterest | 502 | 502 (full) | Indo, Eng | Rp, €, $ |
| SROIE | 973 | 50 | Malay, Eng | RM |
| Unique Data | 20 | 20 (full) | Eng | € |
| **TOTAL** | **5.480** | **~825** | | |

### Keputusan: Mengapa SROIE Box OCR Tidak Dipakai

SROIE menyediakan file `box/*.txt` dengan format:
```
x1,y1,x2,y2,x3,y3,x4,y4,transcript
```

**Masalah:** SROIE box transcripts mengubah semua teks menjadi UPPERCASE, sedangkan gambar aslinya punya mixed case. Ini bertentangan dengan rule `EXACT COPY (CASE SENSITIVE)` — model fine-tuned akan belajar output yang salah.

**Solusi:** Abaikan box files. Gunakan GLM-OCR untuk re-OCR gambar asli SROIE → teks yang akurat sesuai gambar.

### Train/Test Split Strategy

- **Per-source split:** Setiap dataset berkontribusi 5% ke test set
- **Deterministic:** Sort gambar alphabetically → ambil N% terakhir sebagai test
- **Alasan:** Menghindari distribusi skew; setiap sumber terwakili di test

```python
# Implementasi di config.py
def split_train_test(images, test_ratio=0.05):
    n_test = max(1, ceil(len(images) * test_ratio))
    return images[:-n_test], images[-n_test:]  # last N = test
```

### Naming Convention

Format: `{prefix}_{original_stem}.jpg`

| Prefix | Dataset |
|---|---|
| `cord_` | CORD-V2 |
| `erec_` | E-Receipt |
| `expr_` | Express Expense |
| `nano_` | Nanonets |
| `robo_` | Roboflow |
| `pint_` | Pinterest |
| `sroe_` | SROIE |
| `uniq_` | Unique Data |

Contoh: `pint_GAMBAR_0042.jpg`, `cord_GAMBAR_0001.jpg`

---

## 5. Schema Ekstraksi

### Desain Schema

Schema dirancang berdasarkan observasi struktur receipt dari 8 dataset dengan bahasa dan mata uang berbeda.

**Prinsip desain:**
1. **Semua nilai adalah string** — tidak ada integer/float; ambil exactly as written
2. **Monetary amount bersih** — tidak ada simbol mata uang di field amount
3. **Arrays untuk multi-value** — contacts, items, taxes, discounts semuanya array
4. **store_contacts.type = label as-is** — tidak ada klasifikasi "TEL/FAX/EMAIL"
5. **Item-level vs summary-level discount** dipisahkan

```json
EXTRACTION_SCHEMA = {
    "info": {
        "store_name": "",
        "store_location": "",
        "store_contacts": [
            {"type": "", "value": ""}
        ],
        "tax_id": "",
        "receipt_id": "",
        "payment_date": "",
        "payment_time": "",
        "time_unit": ""
    },
    "items": [
        {
            "item_name": "",
            "quantity": "",
            "unit_price": "",
            "discount_label": "",
            "discount_price": "",
            "tax_label": "",
            "total_price": ""
        }
    ],
    "payment": {
        "total_items": "",
        "currency": "",
        "subtotal_price": "",
        "discounts": [
            {"discount_name": "", "amount": ""}
        ],
        "taxes": [
            {"tax_name": "", "amount": ""}
        ],
        "additional_charges": [
            {"charge_name": "", "amount": ""}
        ],
        "grand_total": "",
        "rounding": "",
        "payment_method": "",
        "tendered": "",
        "change": ""
    }
}
```

### Evolusi Schema

| Versi | Perubahan | Alasan |
|---|---|---|
| v1 | Schema awal dari SROIE | Hanya 4 fields dari entities.txt |
| v2 | Tambah `store_contacts` array, `items` array | Multi-contact, multi-item support |
| v3 | Ubah `store_contacts.type` dari klasifikasi ke label as-is | Mencegah hallucination |
| v4 | Tambah `discount_label`, `discount_price`, `tax_label` per item | Retail receipt support |

> ⚠️ **Invariant yang dijaga:** `FEW_SHOT_OUTPUT` selalu harus mirror `EXTRACTION_SCHEMA` secara exact. Verified dengan automated check di test suite.

---

## 6. Perancangan Prompt Engineering

### Tiga Layer Teknik (dari Paper)

```
┌─────────────────────────────────────────┐
│  Layer 3: Prompt Repetition (optional)  │
│  ┌───────────────────────────────────┐  │
│  │  Layer 2: One-Shot Example        │  │
│  │  ┌─────────────────────────────┐  │  │
│  │  │  Layer 1: Field-Specific    │  │  │
│  │  │  Extraction Rules           │  │  │
│  │  └─────────────────────────────┘  │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### Layer 1: Field-Specific Rules

Setiap field kritis punya rule eksplisit. Berikut prompt extraction rules:

```
EXTRACTION_RULES = """
EXTRACTION RULES (read carefully):
- Format output as JSON matching the schema exactly — no extra keys, no missing keys.
- EXACT COPY (CASE SENSITIVE): Copy all text exactly as written. Do not autocorrect or normalize.
- Zero and Placeholder Values: If a label exists but its value is "0", "0.00", or "-", copy it exactly. Do NOT treat as empty.
- Extract ONLY text explicitly written in the receipt. Never calculate, sum, or infer.
- Numbers: copy EXACTLY as written ("193.00", "5.00%", "0.00") — no conversion.
- Clean Numbers: For all price/amount fields, extract ONLY the numeric value. NEVER include currency symbols (Rp, $, RM, €, etc.).
- Strings not found: use "" (empty string).
- Arrays not found: use [] (empty array). Do NOT put empty placeholder objects inside arrays.

receipt_info:
- receipt_id: look for Receipt No, Invoice No, Bill No, Ref No, or similar.
- tax_id: is the store's tax registration number (e.g. NPWP, GST ID).

store_name & store_location:
- store_name: extract the official name of the store as printed on the receipt. This is often at the top and sometimes at the bottom. Also be aware with store include the branch name in the store name (e.g., "ALFAMART Kebayoran Lama"). It make sure included, cause that's not location store.
- store_location: extract the full address of the store as printed on the receipt. This may include street name, number, city, postal code, and other location details. If the receipt only has a general location (e.g., "Jakarta"), copy that as is.

store_contacts:
- Extract the label (e.g., "Tel", "Tel.", "Phone", "Fax", "WA", "Website", etc.) exactly as written into "type".
- If there is NO label for a contact value, "type" MUST be "".
- DO NOT classify or guess the type. No label = empty type, always.
- Example: "Tel.: 07-123" → {"type": "Tel.", "value": "07-123"}
- Example: "Fax: -" (no value) → {"type": "Fax", "value": "-"}
- Example: "www.store.com" (no "Website" label) → {"type": "", "value": "www.store.com"}
- Example: "Fb/Ig: @ayam_kicau" (multi type) → {"type": "Fb", "value": "@ayam_kicau"}, {"type": "Ig", "value": "@ayam_kicau"}

payment_time & time_unit:
- payment_time: Copy only numbers/colon (e.g., "15:34:15", "02:44").
- time_unit: Copy only the unit IF written (e.g., "AM", "PM", "WIB", "UTC", "+07:00", "+08:00"). Otherwise "".
- If multiple times exist, select the chronologically latest time, or pick the one closest to "TOTAL".

items & returned_items:
- item_name: extract ONLY the descriptive product text. DO NOT include internal codes, SKUs, or barcodes.
- quantity: the number of units. Copy only the number — never include "x", "@", "PCS", "*".
- unit_price: price for ONE single unit.
- total_price / total_refund: final extended price for that line.
- discount_label: copy exact text of any per-item discount label (e.g., "DISKON: (20%)", "Member Disc."). Use "" if none.
- discount_price: copy the number printed next to/below discount_label. Include "-" if written. Use "" if none.
- tax_label: tax code or category on the item line (e.g., "SR", "ZRL", "6%"). Use "" if not shown per item.

payment summary:
- total_items: fill ONLY if explicitly written (e.g., "Total Qty", "Item Count"). Do NOT count rows yourself.
- subtotal_price: look for "Subtotal", "Total Sales (Excl. GST)", "Net Amount", "Total (Excl. Tax)".
- currency: symbol ($, Rp, RM, €, etc.) ONLY if printed on receipt. Do not infer from location.
- discount labels and amounts: for each line item that reduces the total price (e.g., 'Discount 35%', 'KOTA HEMAT', 'Voucher', 'Promo Code', 'Total Diskon', 'Total Voucher', or similar), create a separate entry with the exact label as 'discount_name' and the numeric value as 'amount'. Include the negative sign '-' if written.
- taxes: each tax line — exact label → "tax_name", numeric value → "amount" (e.g. tax_name: "GST 6%", amount: "5000", etc) also include total tax if writen.
- additional_charges: service charge, delivery fee, etc. — exact label → "charge_name", value → "amount" (e.g. charge_name: "Biaya perngiriman", amount: "16,000", etc). also include total charge if writen.
- grand_total: final amount paid. Copy exactly as printed. Do NOT calculate.
- payment_method: copy label exactly as written. Do NOT translate (keep "Tunai", not "Cash").
- tendered: amount handed over by customer.
- rounding: include "+" or "-" sign if explicitly written.
- change: amount returned to customer.

DATA PRIVACY: Skip personal names (cashier/customer) and card numbers.
""".strip()
```

### Layer 2: One-Shot Example

Receipt buatan yang mendemonstrasikan **semua edge case** sekaligus:

| Feature dalam One-Shot | Edge Case yang Diajarkan |
|---|---|
| `Tel.: 07-xxx` | type = "Tel." bukan "TEL" |
| `ryuk@gmail.com` (no label) | type = "" |
| `+08:00` di timestamp | time_unit = "+08:00" |
| `MEMBER -9.50` per item | discount_label + discount_price |
| `SR` per item | tax_label per item |
| RETURN ITEM section | returned_items array |
| `Total Qty : 5` | total_items (explicit only) |
| `MEMBER DISC : -5.00` | discounts array |
| `SST 6%` | taxes array |
| `SERVICE CHARGE 5%` | additional_charges array |
| `ROUNDING : +0.02` | rounding dengan tanda positif |
| `currency: ""` | tidak ada simbol RM tercetak |

### Layer 3: Prompt Repetition (Modular)

```python
# config.py — build_kie_prompt()
if PROMPT_REPETITION:
    return core + separator + core   # repeat 2x
return core
```

**Kapan diaktifkan:**

| Model | `PROMPT_REPETITION` | Alasan |
|---|---|---|
| `gemini-3.1-pro-preview` | `false` | Thinking model; reasons internally |
| `gemini-3-flash` | `true` | Non-thinking; butuh repetition |
| `gemini-3-flash` | `true` | Non-thinking |

### System Prompt untuk Gemini

```python
system = (
    "You are a precise receipt information extractor. "
    "Extract ONLY information explicitly visible in the OCR text. "
    "Never calculate, infer, or assume any values. "
    "Output strictly valid JSON matching the provided schema exactly."
)
```

### Perbaikan JSON dari SROIE Experience

Dari validasi normalize_sroie.py, ditemukan 100% failure rate karena:

| Error | Penyebab | Fix |
|---|---|---|
| Unterminated string | Newline literal dalam JSON string | `response_format={"type":"json_object"}` |
| Missing `,` delimiter | Trailing comma | API-level JSON constraint |
| Truncated key | Context window | `max_tokens=8192` |

**Fix utama:** `response_format={"type": "json_object"}` — constraint di level token sampler, bukan parse-time workaround.

**Fallback:** `json_repair` library sebagai layer 2 jika ada edge case residual.

---

## 7. Pipeline Step-by-Step

### Step 1: OCR Extraction (`1_ocr_extractor.py`)

**Input:** Gambar dari 8 source dataset  
**Output:** `{split}/images/*.jpg` + `{split}/ocr/*.txt`

```
Untuk setiap gambar:
  1. Collect dari source path (sorted, deterministic)
  2. Deduplicate (case-insensitive extension matching)
  3. Deterministic 95/5 split per source
  4. Load + convert ke JPEG RGB (cap 4096px)
  5. Skip gambar corrupt (PIL verify + load)
  6. Encode ke base64 data URI
  7. POST ke GLM-OCR vLLM server (24 concurrent)
  8. Save .txt ke ocr/
  9. Checkpoint setiap 50 gambar
  10. Oxen push setelah selesai
```

**Kenapa 24 concurrent workers?**

GLM-OCR adalah model 0.9B. Pada L4 24GB VRAM, model fits beberapa kali lipat dalam VRAM. vLLM batches requests secara internal — cara saturate GPU adalah dengan flood concurrent requests, bukan serial processing.

**GLM-OCR Prompt:**
```
"Text Recognition:"
```
Ini prompt predefined dari GLM-OCR untuk ekstraksi teks mentah (bukan Information Extraction). Menghasilkan teks yang faithful ke gambar termasuk case, spacing, dan layout.

**Kenapa bukan GLM-OCR Information Extraction langsung?**

GLM-OCR sudah support IE prompt `请按下列JSON格式输出图中信息:` tapi untuk training data, kita butuh:
1. **Intermediate OCR text** sebagai bahan verifikasi manual
2. **Gemini Pro** yang reasoning capability-nya jauh lebih baik untuk initial annotation
3. **Human review** yang lebih mudah dengan teks vs gambar

### Step 2: KIE Processing (`2_kie_processor.py`)

**Input:** `{split}/ocr/*.txt`  
**Output:** `{split}/labels/*.json`

```
Untuk setiap .txt file:
  1. Read OCR text
  2. Build prompt (config.build_kie_prompt)
  3. Rate limit check (3s delay, daily budget guard)
  4. POST ke Gemini (response_format=json_object)
  5. Parse JSON (json.loads → json_repair fallback)
  6. Validate schema (deep merge into EXTRACTION_SCHEMA)
  7. Clean empty placeholder arrays
  8. Save .json ke labels/
  9. Checkpoint setiap 10 calls
  10. Stop jika 240 RPD limit tercapai
```

**Daily Budget Strategy:**

```
gemini-3.1-pro-preview Tier 1:
  Max: 250 RPD
  Safe: 240 RPD
  Rate: 3s/request = 20 RPM

Total ~825 gambar ÷ 240/hari = ~3.5 hari minimum

Fallback model: gemini-3-flash (10,000 RPD)
→ Ganti LLM_MODEL di .env, tidak perlu ubah kode
```

**JSON Validation Pipeline:**

```python
raw_response
  → parse_json_response()
      → Layer 1: json.loads()          # primary (json_object mode)
      → Layer 2: json_repair()         # fallback
      → Layer 3: raise with diagnostics
  → validate_and_merge(ai_result)
      → deep_merge ke EXTRACTION_SCHEMA
      → ensure_arrays()
      → clean_empty_arrays()
```

### Step 3: Label Studio Verification (`3_label_studio_converter.py`)

**Input:** `labels/*.json` + `images/*.jpg`  
**Output:** Verified `labels/*.json`

```
Export mode:
  1. Generate tasks.json (Label Studio import format)
  2. Generate labeling_config.xml (UI layout)
  3. Generate VERIFY_REPORT.md (schema issues, common errors)

[Manual review di Label Studio]
  - Lihat gambar receipt asli
  - Bandingkan dengan OCR text (kiri)
  - Edit JSON jika salah (kanan)
  - Set verdict: correct / corrected / skip

Import mode:
  1. Parse Label Studio export JSON
  2. Extract corrected annotation per task
  3. Validate schema
  4. Overwrite labels/*.json
  5. Report: updated / unchanged / skipped / errors
```

**Label Studio UI Layout:**
```
┌──────────────────────────────────────────┐
│  Split: train | Source: cord | File: xxx │
├──────────────────────────────────────────┤
│           Receipt Image (700px)          │
├───────────────────┬──────────────────────┤
│  OCR Text         │  Extracted JSON      │
│  (read-only)      │  (editable)          │
│                   │                      │
│  [raw text dari   │  {"info": {...},     │
│   GLM-OCR]        │   "items": [...],    │
│                   │   "payment": {...}}  │
├──────────────────────────────────────────┤
│  Verdict: ○ correct  ○ corrected  ○ skip │
└──────────────────────────────────────────┘
```

**Common Errors dari Gemini (dari VERIFY_REPORT.md):**

| Error Pattern | Cara Fix |
|---|---|
| Currency symbol dalam price field | Hapus simbol, keep angka saja |
| `store_contacts.type` diklasifikasi padahal unlabelled | Set `type` ke `""` |
| `item_name` include barcode/SKU | Hapus kode, keep deskripsi saja |
| `payment_method` diterjemahkan | Kembalikan ke bahasa asli |

### Step 4: Final Formatter (`4_final_formatter.py`)

**Input:** Verified `labels/*.json` + `images/*.jpg`  
**Output:** LLaMA-Factory ShareGPT format JSON

```
Untuk setiap pair (image, label):
  1. Validate image masih readable (PIL verify + load)
  2. Skip jika corrupt (log, tidak crash)
  3. Load + validate label JSON
  4. ensure_all_schema_keys() (fill missing dengan defaults)
  5. clean_empty_arrays() (hapus placeholder empty dicts)
  6. Build ShareGPT format sample
  7. Compute statistics
  8. Write recipe_db_{split}.json
  9. Patch dataset_info.json
  10. Oxen push
```

**ShareGPT Format (per GLM-OCR fine-tuning guide):**

```json
{
  "messages": [
    {
      "role": "user",
      "content": "<image>请按下列JSON格式输出图中信息:\n{EXTRACTION_SCHEMA}"
    },
    {
      "role": "assistant",
      "content": "{kompact JSON string dari verified label}"
    }
  ],
  "images": ["recipe_db/train/images/cord_GAMBAR_0001.jpg"]
}
```

> **Catatan kritis:** Jumlah tag `<image>` di content **harus sama persis** dengan jumlah entry di `images` array. Mismatch menyebabkan training error.

---

## 8. Workflow End-to-End

### Prerequisites

```bash
# 1. Start GLM-OCR vLLM server
vllm serve zai-org/GLM-OCR \
  --port 8000 \
  --speculative-config.method mtp \
  --speculative-config.num_speculative_tokens 1 \
  --served-model-name zai-org/GLM-OCR

# 2. Verify server
curl -s http://localhost:8000/v1/models | python3 -m json.tool

# 3. Set environment
cp .env.example .env
# Edit .env: LLM_API_KEY, OXEN_AUTH_TOKEN
```

### Jalankan Pipeline

```bash
cd fine-tuning-glm-ocr

# ── STEP 1: OCR Extraction ──────────────────────────────────────────
# Test 3 gambar dulu
python raw_data/scripts/recipe_db/1_ocr_extractor.py --mode validate

# Inspect hasil
cat LLaMA-Factory/data/recipe_db/train/ocr/cord_*.txt | head -20

# Full run (checkpoint-resumable, aman di-interrupt)
python raw_data/scripts/recipe_db/1_ocr_extractor.py --mode run

# Single source jika mau test per-source
python raw_data/scripts/recipe_db/1_ocr_extractor.py --mode run --source pinterest


# ── STEP 2: KIE Extraction ─────────────────────────────────────────
# Cek budget dulu
python raw_data/scripts/recipe_db/2_kie_processor.py --status

# Test 3 file
python raw_data/scripts/recipe_db/2_kie_processor.py --mode validate

# Inspect hasil
cat LLaMA-Factory/data/recipe_db/train/labels/cord_*.json | python3 -m json.tool | head -40

# Full run (stops at 240 RPD, resume next day)
python raw_data/scripts/recipe_db/2_kie_processor.py --mode run

# Kalau Gemini Pro limit habis, switch ke flash di .env:
# LLM_MODEL=gemini-3-flash
# PROMPT_REPETITION=true    ← aktifkan untuk non-thinking model
python raw_data/scripts/recipe_db/2_kie_processor.py --mode run


# ── STEP 3: Manual Verification ────────────────────────────────────
# Generate schema report (sebelum buka Label Studio)
python raw_data/scripts/recipe_db/3_label_studio_converter.py --mode report

# Buka report
cat label_studio/VERIFY_REPORT.md

# Export ke Label Studio
python raw_data/scripts/recipe_db/3_label_studio_converter.py --mode export

# Jalankan Label Studio
LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true \
LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT=/ \
label-studio start --port 8081

# Di browser:
# 1. Create project
# 2. Settings → Labeling Interface → paste isi label_studio/labeling_config.xml
# 3. Import → upload label_studio/tasks.json
# 4. Review semua task
# 5. Export → JSON-MIN → simpan sebagai label_studio_export.json

# Import corrections
python raw_data/scripts/recipe_db/3_label_studio_converter.py \
  --mode import \
  --file label_studio_export.json


# ── STEP 4: Final Formatting ────────────────────────────────────────
# Inspect 5 sample output
python raw_data/scripts/recipe_db/4_final_formatter.py --mode validate

# Full run
python raw_data/scripts/recipe_db/4_final_formatter.py --mode run

# Lihat statistik
python raw_data/scripts/recipe_db/4_final_formatter.py --mode stats


# ── STEP 5: Fine-Tuning ─────────────────────────────────────────────
cd LLaMA-Factory

# Verify dataset terdaftar
cat data/dataset_info.json | python3 -m json.tool | grep recipe_db

# LoRA fine-tuning (L4 24GB, ~8GB VRAM needed)
DISABLE_VERSION_CHECK=1 CUDA_VISIBLE_DEVICES=0 \
  llamafactory-cli train config/glm_ocr_lora_sft.yaml

# Monitor training
tail -f saves/glm-ocr/lora/sft/trainer_log.jsonl
```

### Estimasi Waktu

| Step | Estimasi | Bottleneck |
|---|---|---|
| OCR Extraction (~825 gambar) | ~20 menit | L4 GPU, 24 concurrent |
| KIE Extraction | ~3-4 hari | 240 RPD Gemini limit |
| Manual Review | ~4-6 jam | Human review speed |
| Final Formatting | ~2 menit | I/O only |
| LoRA Fine-tuning | ~2-4 jam | L4 GPU |

---

## 9. Struktur File & Direktori

```
fine-tuning-glm-ocr/
├── .env                          ← API keys & config
├── .oxen/                        ← Oxen repository metadata
├── pyproject.toml                ← Python dependencies
│
├── raw_data/
│   ├── cord-v2/images/train/     ← Source images
│   ├── e_receipt/images/
│   ├── expressexpense/images/
│   ├── nanonets/images/
│   ├── roboflow/train/images/
│   ├── pinterest/images/
│   ├── sroie/train/img/
│   ├── uniquedata/images/
│   │
│   └── scripts/recipe_db/
│       ├── config.py             ← Single source of truth
│       ├── 1_ocr_extractor.py    ← GLM-OCR via vLLM
│       ├── 2_kie_processor.py    ← Gemini KIE extraction
│       ├── 3_label_studio_converter.py  ← Manual review
│       └── 4_final_formatter.py  ← LLaMA-Factory format
│
├── LLaMA-Factory/
│   ├── config/
│   │   ├── glm_ocr_lora_sft.yaml
│   │   └── glm_ocr_full_sft.yaml
│   └── data/
│       ├── recipe_db/
│       │   ├── train/
│       │   │   ├── images/  *.jpg
│       │   │   ├── ocr/     *.txt
│       │   │   └── labels/  *.json
│       │   └── test/
│       │       ├── images/
│       │       ├── ocr/
│       │       └── labels/
│       ├── recipe_db_train.json  ← LLaMA-Factory training data
│       ├── recipe_db_test.json   ← LLaMA-Factory test data
│       └── dataset_info.json     ← Dataset registry (auto-patched)
│
├── label_studio/
│   ├── tasks.json                ← Import ke Label Studio
│   ├── labeling_config.xml       ← Paste ke project settings
│   └── VERIFY_REPORT.md          ← Schema issues & checklist
│
├── checkpoints/recipe_db/
│   ├── ocr_extractor.json        ← Step 1 resume state
│   └── kie_processor.json        ← Step 2 resume state + budget
│
└── logs/recipe_db/
    ├── 1_ocr_extractor.log
    ├── 2_kie_processor.log
    ├── 3_label_studio_converter.log
    └── 4_final_formatter.log
```

---

## 10. Konfigurasi Environment

### `.env`

```properties
# ─── LLM untuk KIE Extraction (Gemini) ───────────────────────────
LLM_PROVIDER=openai
LLM_ENDPOINT=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_MODEL=gemini-3.1-pro-preview
# Rate limits: 25 RPM | 1M TPM | 250 RPD
LLM_API_KEY=

LLM_TEMPERATURE=0.0

# ─── GLM-OCR via vLLM (local) ─────────────────────────────────────
GLM_ENDPOINT=http://localhost:8000/v1
GLM_MODEL=zai-org/GLM-OCR

# ─── Prompt Repetition ────────────────────────────────────────────
# false = thinking model (gemini-3.1-pro-preview)
# true  = non-thinking model (gemini-3-flash, gemini-2.5-flash)
PROMPT_REPETITION=false

# ─── Oxen Versioning ──────────────────────────────────────────────
OXEN_REMOTE=https://hub.oxen.ai/Laoode/RECIPE-DB
OXEN_AUTH_TOKEN=
```

### Model Fallback Strategy

```
Gemini 3.1 Pro Preview (default)
  │  250 RPD limit tercapai
  ▼
Gemini 3 Flash (fallback)
  │  Ganti LLM_MODEL + aktifkan PROMPT_REPETITION=true
  │  10,000 RPD — selesaikan semua data dalam 1 hari
  ▼
Dataset complete
```

---

## 11. Rate Limiting & Budget Strategy

### Gemini 3.1 Pro Preview (Tier 1)

| Limit | Max | Safe Margin | Implementasi |
|---|---|---|---|
| RPM | 25 | 20 | `KIE_DELAY_SECONDS = 3.0s` |
| RPD | 250 | 240 | Daily counter di checkpoint |
| TPM | 1M | - | Tidak ditrack (schema kecil) |

### Daily Budget Guard

```python
# 2_kie_processor.py
def get_today_count(ckpt):
    return ckpt["budget"].get(str(date.today()), 0)

def budget_remaining(ckpt):
    return KIE_RPD_LIMIT - get_today_count(ckpt)

# Setiap request increment counter
increment_budget(ckpt)

# Stop jika limit tercapai
if budget_remaining(ckpt) <= 0:
    logger.warning("Daily limit reached. Resume tomorrow.")
    break
```

Status budget bisa dilihat kapan saja:
```bash
python 2_kie_processor.py --status
```

### Checkpoint Design

```json
{
  "processed": ["cord_00001", "cord_00002", ...],
  "failed": ["pint_00123"],
  "budget": {
    "2026-03-01": 240,
    "2026-03-02": 198
  }
}
```

Resume otomatis: script skip semua stem yang sudah ada di `processed`.

---

## 12. Versioning Dataset dengan Oxen

Oxen digunakan karena dataset mencakup ribuan gambar binary — sesuatu yang Git tidak handle dengan baik.

### Initial Setup

```bash
# Di project root
oxen init
oxen config --auth hub.oxen.ai YOUR_AUTH_TOKEN
oxen config --set-remote origin https://hub.oxen.ai/Laoode/RECIPE-DB

# First push
echo "# RECIPE-DB" >> README.md
oxen add README.md
oxen commit -m "init: create RECIPE-DB repository"
oxen push origin main
```

### Automated Push dalam Pipeline

Setiap step push otomatis setelah selesai:

```python
# Semua steps memanggil oxen_push() setelah batch complete
oxen_push("feat(recipe-db): add OCR results — 825 images")
oxen_push("feat(recipe-db): add KIE labels batch — 240 labels (240/825)")
oxen_push("feat(recipe-db): final LLaMA-Factory dataset — train=785 test=40")
```

### Versioning Strategy

| Commit | Isi | Kapan |
|---|---|---|
| `init: create RECIPE-DB` | README | Sekali |
| `feat: add OCR results` | images/ + ocr/ | Setelah step 1 |
| `feat: add KIE labels batch` | labels/ (per hari) | Setiap step 2 run |
| `fix: verified labels` | labels/ (corrected) | Setelah step 3 import |
| `feat: final LLaMA-Factory dataset` | recipe_db_*.json | Setelah step 4 |

---

## 13. Design Decisions & Trade-offs

### Keputusan ku: Synthetic Annotation vs Human Annotation

**Pilihan:** Gemini Pro sebagai annotator vs. human annotation from scratch

**Trade-off:**
- ✓ Jauh lebih cepat dan murah untuk ~825 gambar
- ✓ Gemini Pro sangat baik untuk structured extraction
- ✗ Butuh manual review untuk koreksi errors
- ✗ Dibatasi oleh kualitas OCR dari GLM-OCR

**Mitigasi:** Manual review via Label Studio sebagai quality gate.

---

*Dokumentasi ini mencerminkan state pipeline per Maret 2026. Update schema atau rules harus diikuti update `FEW_SHOT_OUTPUT` dan verifikasi ulang invariant test.*