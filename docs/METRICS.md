### 3.x Data Specification

Sistem Klaudia dirancang untuk memproses struk belanja dalam berbagai format, bahasa, dan mata uang. Setiap citra struk dianotasi menggunakan skema ekstraksi terstruktur yang mendefinisikan hierarki entitas informasi dari metadata toko hingga rincian pembayaran. Skema ini terdiri dari empat superclass utama yang mencakup seluruh informasi relevan pada struk, sebagaimana diilustrasikan pada Gambar 3.x dan dirangkum dalam Tabel 3.x.

> **Gambar 3.x** An example of receipt image (left) and its structured JSON output (right).
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
    "returned_items": [
        {
            "item_name": "",
            "quantity": "",
            "unit_price": "",
            "total_refund": ""
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

**Tabel 3.x** Class Definition

| No. | Superclass | # Subclasses | Description |
|-----|------------|:------------:|-------------|
| 1 | `info` | 8 | Metadata toko dan transaksi |
| 2 | `items` | 7 | Rincian barang dibeli |
| 3 | `returned_items` | 4 | Rincian barang dikembalikan |
| 4 | `payment` | 11 | Ringkasan dan total pembayaran |

---

### B. Skenario Evaluasi Kualitas Ekstraksi

Evaluasi kualitas ekstraksi dilakukan secara kuantitatif menggunakan dua metrik utama: KIEval dan ANLS\*. Kedua metrik ini dipilih karena saling melengkapi — KIEval mengukur ketepatan pada level pasangan entitas secara diskrit, sedangkan ANLS\* mengukur kemiripan karakter secara kontinu sehingga lebih toleran terhadap kesalahan penulisan minor. Untuk keperluan verifikasi dan transparansi, berikut disajikan perhitungan manual dari kedua metrik menggunakan contoh ilustrasi pada Gambar 3.x.

Gambar 3.x: Contoh Ilustrasi Ground-Truth dan Hasil Prediksi GLM-OCR
---
```
TOYIB JAYA
JL. POROS BTN TAMANG ALUN II
BELAKANG BTN KENDARI PERMAI
KENDARI
PEMBELI:

KASIR   : KASIR

TGL     : 07/03/2026        No.R43-0703261230
          23.54.00

-----------------------------------------------
QTY Sat Nama barang        Harga        Jlh
-----------------------------------------------
2 PCS INDOMIE KALDU AYA    3.500        7.000
4 PCS INDOMIE RASA COTO    3.500       14.000
1 PCS ULTRA MILK LOW FA    8.500        8.500

-----------------------------------------------
Total Qty   : 7
Total       : 29.500
Bayar       : 29.500

Kembali :

Terima Kasih !!! Silahkan Datang Kembali
Barang yang dibeli tidak dapat dikembalikan.
```
-----------------------------------------------------
**Ground-truth**

| items.name | items.quantity | items.total_price |
|---|---|---|
| 🔵 INDOMIE KALDU AYA | 🔵 2 | 🔵 7.000 |
| 🔵 INDOMIE RASA COTO | 🔵 4 | 🔵 14.000 |
| 🔵 ULTRA MILK LOW FA | 🔵 1 | 🔵 8.500 |

| payment.total_items | payment.grand_total | payment.tendered |
|---|---|---|
| 🔵 7 | 🔵 29.500 | 🔵 29.500 |

**Prediction**

| items.name | items.quantity | items.total_price |
|---|---|---|
| 🔴 INDOMIE KALDU AYAM | 🔵 2 | 🔵 7.000  |
| 🔵 INDOMIE RASA COTO | 🔵 4 | 🔵 14.000 |
| 🔵 ULTRA MILK LOW FA | 🔵 1 | 🔴 8.600  |

| payment.total_items | payment.grand_total | payment.tendered |
|---|---|---|
| 🔵 7 | 🔵 29.500 | 🔵 29.500 |

🔵 True 🔴 False
---
Gambar 3.x: Contoh Ilustrasi Ground-Truth dan Hasil Prediksi GLM-OCR

#### B.1. Perhitungan Manual KIEval

KIEval mengevaluasi kualitas ekstraksi informasi kunci pada dua level sekaligus, yaitu level entitas (*entity-level*) dan level grup (*group-level*), dengan terlebih dahulu melakukan pencocokan struktural antar grup sebelum menghitung statistik evaluasi. Berbeda dengan Entity F1 konvensional yang mengevaluasi setiap pasangan *(key, value)* secara independen, KIEval mempertimbangkan relasi kontekstual antar entitas dalam satu grup yang sama.

Berdasarkan skema ekstraksi pada Gambar 3.x, struktur data diklasifikasikan menjadi dua jenis grup sebagai berikut.

**Tabel 3.x** Struktur Grup Ground-Truth dan Prediksi

| Jenis Grup | ID Grup | Entitas yang Dievaluasi |
|---|---|---|
| Non-grup (payment) | Grup 0 | `payment.total_items`, `payment.grand_total`, `payment.tendered` |
| Grup items | Grup 1 | `items.name`, `items.quantity`, `items.total_price` (baris 1) |
| Grup items | Grup 2 | `items.name`, `items.quantity`, `items.total_price` (baris 2) |
| Grup items | Grup 3 | `items.name`, `items.quantity`, `items.total_price` (baris 3) |

Sesuai definisi KIEval, entitas non-grup (`payment`) dimasukkan ke dalam Grup 0 sebagai grup khusus, sementara setiap baris `items` diperlakukan sebagai satu unit grup tersendiri.

---

##### Langkah 1 — Hungarian Matching Antar Grup

Sebelum menghitung statistik evaluasi, dilakukan pencocokan (*matching*) antara grup prediksi dan grup ground-truth menggunakan algoritma Hungarian. Skor pencocokan $S_{(n,m)}$ dihitung sebagai jumlah entitas yang identik antara grup prediksi ke-$n$ dan grup ground-truth ke-$m$.

**Tabel 3.x** Matriks Skor Pencocokan $S_{(n,m)}$ untuk Grup Items

| | GT Grup 1 (AYA) | GT Grup 2 (COTO) | GT Grup 3 (MILK) |
|---|:---:|:---:|:---:|
| **Pred Grup 1 (AYAM)** | **2** | 0 | 0 |
| **Pred Grup 2 (COTO)** | 0 | **3** | 0 |
| **Pred Grup 3 (MILK)** | 0 | 0 | **2** |

Hasil Hungarian matching menghasilkan pasangan optimal sebagai berikut.

**Tabel 3.x** Hasil Pasangan Grup Setelah Hungarian Matching

| Pasangan $\mathbf{G}$ | Grup Prediksi | Grup Ground-Truth | Keterangan |
|---|---|---|---|
| $(n_0, m_0)$ | payment (Pred) | payment (GT) | Non-grup |
| $(n_1, m_1)$ | items baris 1 (AYAM) | items baris 1 (AYA) | Grup items |
| $(n_2, m_2)$ | items baris 2 (COTO) | items baris 2 (COTO) | Grup items |
| $(n_3, m_3)$ | items baris 3 (MILK) | items baris 3 (MILK) | Grup items |

---

##### Langkah 2 — Perhitungan KIEval Entity F1

KIEval Entity F1 menghitung statistik TP, FN, dan FP pada level entitas dalam konteks grup yang sudah dipasangkan. Setiap entitas dievaluasi menggunakan *exact match* di dalam grup yang telah dicocokkan.

**Tabel 3.x** Perhitungan TP, FP, FN per Entitas pada Setiap Pasangan Grup

| Pasangan Grup | Entitas | GT | Prediksi | $S^e_{(n,m)}$ | TP | FP | FN |
|---|---|---|---|:---:|:---:|:---:|:---:|
| $(n_0, m_0)$ payment | `total_items` | 7 | 7 | 1 | 1 | 0 | 0 |
| | `grand_total` | 29.500 | 29.500 | 1 | 1 | 0 | 0 |
| | `tendered` | 29.500 | 29.500 | 1 | 1 | 0 | 0 |
| $(n_1, m_1)$ items baris 1 | `item_name` | INDOMIE KALDU AYA | INDOMIE KALDU AYAM | 0 | 0 | 1 | 1 |
| | `quantity` | 2 | 2 | 1 | 1 | 0 | 0 |
| | `total_price` | 7.000 | 7.000 | 1 | 1 | 0 | 0 |
| $(n_2, m_2)$ items baris 2 | `item_name` | INDOMIE RASA COTO | INDOMIE RASA COTO | 1 | 1 | 0 | 0 |
| | `quantity` | 4 | 4 | 1 | 1 | 0 | 0 |
| | `total_price` | 14.000 | 14.000 | 1 | 1 | 0 | 0 |
| $(n_3, m_3)$ items baris 3 | `item_name` | ULTRA MILK LOW FA | ULTRA MILK LOW FA | 1 | 1 | 0 | 0 |
| | `quantity` | 1 | 1 | 1 | 1 | 0 | 0 |
| | `total_price` | 8.500 | 8.600 | 0 | 0 | 1 | 1 |

Akumulasi statistik keseluruhan:

$$TP^{\text{entity}} = 10, \quad FP^{\text{entity}} = 2, \quad FN^{\text{entity}} = 2$$

Nilai Precision, Recall, dan KIEval Entity F1 dihitung sebagai berikut.

$$\text{Precision} = \frac{10}{10 + 2} = \frac{10}{12} \approx 0{,}833$$

$$\text{Recall} = \frac{10}{10 + 2} = \frac{10}{12} \approx 0{,}833$$

$$\textbf{KIEval Entity F1} = \frac{2 \times 0{,}833 \times 0{,}833}{0{,}833 + 0{,}833} = 0{,}833$$

---

##### Langkah 3 — Perhitungan KIEval Group F1

KIEval Group F1 mengevaluasi pada level grup, di mana satu grup dihitung sebagai TP hanya apabila **seluruh entitas** di dalam grup tersebut cocok secara sempurna dengan ground-truth. Evaluasi ini dilakukan pada $\mathbf{G'} = \mathbf{G} \setminus (n_0, m_0)$, yaitu mengecualikan Grup 0 (non-grup payment).

**Tabel 3.x** Evaluasi Kebenaran Setiap Grup pada KIEval Group F1

| Pasangan Grup | Kondisi Seluruh Entitas Identik | Status |
|---|---|:---:|
| $(n_1, m_1)$ items baris 1 | `item_name` tidak cocok (AYA vs AYAM) | Bukan TP |
| $(n_2, m_2)$ items baris 2 | Semua entitas cocok | TP |
| $(n_3, m_3)$ items baris 3 | `total_price` tidak cocok (8.500 vs 8.600) | Bukan TP |

$$TP^{\text{group}} = 1, \quad FP^{\text{group}} = 2, \quad FN^{\text{group}} = 2$$

$$\text{Precision} = \frac{1}{1 + 2} = \frac{1}{3} \approx 0{,}333$$

$$\text{Recall} = \frac{1}{1 + 2} = \frac{1}{3} \approx 0{,}333$$

$$\textbf{KIEval Group F1} = \frac{2 \times 0{,}333 \times 0{,}333}{0{,}333 + 0{,}333} = 0{,}333$$

---

##### Langkah 4 — Perhitungan KIEval Aligned

KIEval Aligned memformulasikan kesalahan prediksi dalam bentuk biaya koreksi, yaitu jumlah langkah *substitution* (Subs), *addition* (Add), dan *deletion* (Del) yang diperlukan untuk mengubah prediksi menjadi ground-truth.

**Tabel 3.x** Perhitungan Biaya Koreksi per Entitas

| Pasangan Grup | Entitas | FP | FN | Subs | Add | Del | Error |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| $(n_1, m_1)$ | `item_name` | 1 | 1 | 1 | 0 | 0 | **1** |
| | `quantity` | 0 | 0 | 0 | 0 | 0 | 0 |
| | `total_price` | 0 | 0 | 0 | 0 | 0 | 0 |
| $(n_2, m_2)$ | semua entitas | 0 | 0 | 0 | 0 | 0 | 0 |
| $(n_3, m_3)$ | `item_name` | 0 | 0 | 0 | 0 | 0 | 0 |
| | `quantity` | 0 | 0 | 0 | 0 | 0 | 0 |
| | `total_price` | 1 | 1 | 1 | 0 | 0 | **1** |
| $(n_0, m_0)$ payment | semua entitas | 0 | 0 | 0 | 0 | 0 | 0 |
| **Total** | | | | **2** | **0** | **0** | **2** |

Tidak terdapat grup yang tidak tercocokkan (*unmatched*) sehingga suku kedua dan ketiga pada persamaan Error bernilai nol. Total error koreksi dihitung sebagai berikut.

$$\text{Error} = 2 + 0 + 0 = 2$$

$$\textbf{KIEval}_{\textbf{Aligned}} = \frac{TP^{\text{entity}}}{TP^{\text{entity}} + \text{Error}} = \frac{10}{10 + 2} = \frac{10}{12} \approx 0{,}833$$

---

##### Rangkuman Hasil Perhitungan KIEval

**Tabel 3.x** Rekapitulasi Nilai KIEval pada Contoh Gambar 3.x

| Metrik | Nilai | Interpretasi |
|---|:---:|---|
| KIEval Entity F1 | **0,833** | 10 dari 12 entitas terekstrak dengan benar dalam konteks grup yang tepat |
| KIEval Group F1 | **0,333** | Hanya 1 dari 3 grup items terekstrak secara utuh dan benar |
| KIEval Aligned | **0,833** | Dibutuhkan 2 langkah koreksi dari total 12 entitas yang diprediksi |


Hasil perhitungan menunjukkan bahwa KIEval Group F1 memberikan penilaian yang paling ketat, yaitu **0,333**, karena menuntut kebenaran seluruh entitas dalam satu baris item secara bersamaan. Sementara itu, KIEval Entity F1 dan KIEval Aligned menghasilkan nilai yang sama sebesar **0,833**, yang mencerminkan bahwa dari 12 entitas yang dievaluasi, terdapat 2 kesalahan, yaitu halusinasi karakter pada nama produk pertama (*INDOMIE KALDU AYAM* vs *INDOMIE KALDU AYA*) dan kesalahan digit pada harga item ketiga (*8.600* vs *8.500*). Kedua kesalahan tersebut masing-masing diperlakukan sebagai satu langkah substitusi dalam KIEval Aligned, sesuai dengan biaya koreksi yang akan dikeluarkan dalam skenario aplikasi nyata.

---

#### B.2 Perhitungan Manual ANLS*

ANLS* mengevaluasi kualitas ekstraksi informasi kunci dengan mengukur kemiripan karakter secara kontinu menggunakan *Normalized Levenshtein Similarity* (NLS). Berbeda dengan KIEval yang menggunakan *exact match*, ANLS* memberikan nilai parsial untuk prediksi yang hampir benar sehingga lebih toleran terhadap kesalahan penulisan minor akibat proses OCR. Metrik ini mendukung tipe data String, List, Dict, Tuple, dan None secara rekursif, sehingga mampu mengevaluasi struktur bersarang (*nested*) secara menyeluruh.

Secara formal, ANLS* didefinisikan sebagai berikut.

$$\text{ANLS*}(g, p) = \frac{s(g, p)}{l(g, p)}$$

dengan $s$ adalah skor kemiripan antara ground-truth $g$ dan prediksi $p$, serta $l$ adalah panjang normalisasi pohon (*tree*) kedua nilai tersebut, sehingga $\text{ANLS*} \in [0, 1]$.

Berdasarkan contoh pada Gambar 3.17, struktur data yang dievaluasi direpresentasikan sebagai pohon hierarki sebagai berikut.

```
Dict (top-level)
├── "items" : List
│     ├── Dict { item_name, quantity, total_price }  ← baris 1
│     ├── Dict { item_name, quantity, total_price }  ← baris 2
│     └── Dict { item_name, quantity, total_price }  ← baris 3
└── "payment" : Dict
      ├── total_items
      ├── grand_total
      └── tendered
```

---

##### B.2.1 Langkah 1 - Dekomposisi Struktur dan Tipe Data

Sebelum menghitung skor, setiap nilai dalam ground-truth dan prediksi dipetakan ke tipe data yang sesuai dalam ANLS*.

**Tabel 3.x** Pemetaan Tipe Data ANLS* pada Struktur Evaluasi

| Node | Tipe ANLS* | Alasan |
|---|---|---|
| Top-level output | Dict | Memiliki beberapa kunci tetap |
| `items` | List of Dicts | Urutan tidak penting, semua elemen harus ada |
| Setiap baris item | Dict | Terdiri dari pasangan kunci-nilai tetap |
| `item_name`, `quantity`, `total_price` | String | Nilai teks yang dibandingkan karakter per karakter |
| `payment` | Dict | Kunci tetap tanpa urutan |
| `total_items`, `grand_total`, `tendered` | String | Nilai teks yang dibandingkan karakter per karakter |

---

##### B.2.2 Langkah 2 - Hungarian Matching pada Level List

Karena `items` bertipe List, ANLS* menggunakan algoritma Hungarian untuk menentukan pasangan optimal antara setiap elemen ground-truth dan prediksi berdasarkan skor ANLS* pairwise.

Skor ANLS* pairwise dihitung terlebih dahulu untuk setiap kombinasi pasangan Dict item.

**Tabel 3.x** Matriks Skor ANLS* Pairwise Antar Item

| | Pred Baris 1 (AYAM) | Pred Baris 2 (COTO) | Pred Baris 3 (MILK) |
|---|:---:|:---:|:---:|
| **GT Baris 1 (AYA)** | **0,981** | 0,222 | 0,200 |
| **GT Baris 2 (COTO)** | 0,222 | **1,000** | 0,167 |
| **GT Baris 3 (MILK)** | 0,200 | 0,167 | **0,933** |

Hasil Hungarian matching memilih pasangan dengan jumlah skor tertinggi, yaitu diagonal utama dengan total skor $0{,}981 + 1{,}000 + 0{,}933 = 2{,}914$. Pasangan yang terbentuk adalah GT Baris 1 dengan Pred Baris 1, GT Baris 2 dengan Pred Baris 2, dan GT Baris 3 dengan Pred Baris 3. Tidak terdapat elemen yang tidak tercocokkan (*unmatched*) karena jumlah elemen GT dan prediksi sama.

---

##### B.2.3 Langkah 3 - Perhitungan NLS per Field String

Untuk setiap pasangan yang sudah dicocokkan, skor $s$ pada level String dihitung menggunakan rumus berikut.

$$s(g, p) = \begin{cases} 1{,}0 - \dfrac{\text{LD}(g, p)}{\max(|g|, |p|)} & \text{jika NLS} \geq \tau \\ 0{,}0 & \text{jika NLS} < \tau \end{cases}$$

dengan $\tau = 0{,}5$ sebagai ambang batas, dan LD adalah *Levenshtein Distance*.

**Tabel 3.x** Perhitungan NLS per Field pada Setiap Pasangan yang Dicocokkan

| Pasangan | Field | GT | Prediksi | LD | max($\|g\|$, $\|p\|$) | NLS | $\geq \tau$? | $s$ |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| Baris 1 | `item_name` | INDOMIE KALDU AYA | INDOMIE KALDU AYAM | 1 | 18 | 0,944 | Ya | **0,944** |
| | `quantity` | 2 | 2 | 0 | 1 | 1,000 | Ya | **1,000** |
| | `total_price` | 7.000 | 7.000 | 0 | 5 | 1,000 | Ya | **1,000** |
| Baris 2 | `item_name` | INDOMIE RASA COTO | INDOMIE RASA COTO | 0 | 18 | 1,000 | Ya | **1,000** |
| | `quantity` | 4 | 4 | 0 | 1 | 1,000 | Ya | **1,000** |
| | `total_price` | 14.000 | 14.000 | 0 | 6 | 1,000 | Ya | **1,000** |
| Baris 3 | `item_name` | ULTRA MILK LOW FA | ULTRA MILK LOW FA | 0 | 17 | 1,000 | Ya | **1,000** |
| | `quantity` | 1 | 1 | 0 | 1 | 1,000 | Ya | **1,000** |
| | `total_price` | 8.500 | 8.600 | 1 | 5 | 0,800 | Ya | **0,800** |
| **payment** | `total_items` | 7 | 7 | 0 | 1 | 1,000 | Ya | **1,000** |
| | `grand_total` | 29.500 | 29.500 | 0 | 6 | 1,000 | Ya | **1,000** |
| | `tendered` | 29.500 | 29.500 | 0 | 6 | 1,000 | Ya | **1,000** |

Catatan pada field `item_name` baris 1: `"INDOMIE KALDU AYA"` memiliki 17 karakter dan `"INDOMIE KALDU AYAM"` memiliki 18 karakter. LD = 1 karena hanya terdapat satu penyisipan karakter `'M'` di akhir string. Nilai NLS = $1 - 1/18 \approx 0{,}944$ masih berada di atas ambang batas $\tau = 0{,}5$, sehingga mendapat skor parsial dan tidak di-*zero-kan*.

---

##### B.2.4 Langkah 4 - Agregasi Skor $s$ dan Panjang $l$

Skor $s$ dan panjang $l$ diagregasi secara rekursif dari level String ke atas hingga level top-level Dict.

**Agregasi pada Level Dict per Baris Item:**

$$s(\text{baris 1}) = 0{,}944 + 1{,}000 + 1{,}000 = 2{,}944 \quad;\quad l(\text{baris 1}) = 3$$

$$s(\text{baris 2}) = 1{,}000 + 1{,}000 + 1{,}000 = 3{,}000 \quad;\quad l(\text{baris 2}) = 3$$

$$s(\text{baris 3}) = 1{,}000 + 1{,}000 + 0{,}800 = 2{,}800 \quad;\quad l(\text{baris 3}) = 3$$

**Agregasi pada Level List `items`:**

Karena tidak terdapat elemen yang tidak tercocokkan (*unmatched*), suku penalti bernilai nol.

$$s(\text{items}) = 2{,}944 + 3{,}000 + 2{,}800 = 8{,}744 \quad;\quad l(\text{items}) = 3 + 3 + 3 = 9$$

**Agregasi pada Level Dict `payment`:**

$$s(\text{payment}) = 1{,}000 + 1{,}000 + 1{,}000 = 3{,}000 \quad;\quad l(\text{payment}) = 3$$

**Agregasi pada Level Top-Level Dict:**

$$s_{\text{total}} = s(\text{items}) + s(\text{payment}) = 8{,}744 + 3{,}000 = 11{,}744$$

$$l_{\text{total}} = l(\text{items}) + l(\text{payment}) = 9 + 3 = 12$$

---

##### B.2.5 Langkah 5 - Perhitungan ANLS* Final

$$\boxed{\text{ANLS*} = \frac{s_{\text{total}}}{l_{\text{total}}} = \frac{11{,}744}{12} \approx 0{,}979}$$

---

##### Rangkuman Hasil Perhitungan ANLS*

**Tabel 3.x** Rekapitulasi Kontribusi Setiap Komponen terhadap ANLS*

| Komponen | $s$ | $l$ | Kontribusi ANLS* |
|---|:---:|:---:|:---:|
| items baris 1 (AYA vs AYAM) | 2,944 | 3 | 0,981 |
| items baris 2 (semua benar) | 3,000 | 3 | 1,000 |
| items baris 3 (8.500 vs 8.600) | 2,800 | 3 | 0,933 |
| payment (semua benar) | 3,000 | 3 | 1,000 |
| **Total** | **11,744** | **12** | **0,979** |

Hasil perhitungan menunjukkan bahwa model memperoleh nilai ANLS* sebesar **0,979** (97,9%). Nilai ini lebih tinggi dibandingkan KIEval Entity F1 (0,833) karena ANLS* memberikan skor parsial pada field yang hampir benar. Secara khusus, kesalahan pada `item_name` baris 1 (*AYAM* vs *AYA*) tidak di-*zero-kan* melainkan mendapat skor 0,944, dan kesalahan digit pada `total_price` baris 3 (*8.600* vs *8.500*) mendapat skor 0,800. Kedua kondisi ini masih berada di atas ambang batas $\tau = 0{,}5$, sehingga skor parsial tetap diberikan. Hal ini mencerminkan karakteristik ANLS* yang lebih toleran terhadap kesalahan minor akibat proses OCR pada model kecil seperti GLM-OCR 0.9B.