3.5.5 Spesifikasi Data
Sistem Klaudia dirancang untuk memproses struk belanja dalam berbagai format. Setiap citra struk dianotasi menggunakan skema ekstraksi terstruktur yang mendefinisikan hierarki entitas informasi dari metadata toko hingga rincian pembayaran. Struktur skema ekstrasi dan hasil output diliat pada Gambar 3.17-3.18.

<img>Receipt and Code Snippets</img>

Gambar 3.17 Contoh gambar struk pembelian, skema ekstrasi

{
  "info": {
    "store_name": "TOYIB JAYA",
    "store_location": "JL. POROS BTN TAWANG ALUN II BELAKANG BTN KENDARI PERMAI KENDARI",
    "store_contacts": [],
    "tax_id": "",
    "receipt_id": "R43-0703261230",
    "payment_date": "07/03/2026",
    "payment_time": "23.54.00",
    "time_unit": ""
  },
  "items": [
    {
      "item_name": "INDOMIE KALDU AYA",
      "quantity": "2",
      "unit_price": "3.500",
      "discount_label": "",
      "discount_price": "",
      "tax_label": "",
      "total_price": "7.000"
    },
    {
      "item_name": "INDOMIE RASA COTO",
      "quantity": "4",
      "unit_price": "3.500",
      "discount_label": "",
      "discount_price": "",
      "tax_label": "",
      "total_price": "14.000"
    },
    {
      "item_name": "ULTRA MILK LOW FA",
      "quantity": "1",
      "unit_price": "8.500",
      "discount_label": "",
      "discount_price": "",
      "tax_label": "",
      "total_price": "8.500"
    }
  ],
  "returned_items": [],
  "payment": {
    "total_items": "7",
    "currency": "",
    "subtotal_price": "",
    "discounts": [],
    "taxes": [],
    "additional_charges": [],
    "grand_total": "29.500",
    "rounding": "",
    "payment_method": "",
    "tendered": "29.500",
    "change": ""
  }
}
Gambar 3. 18 Contoh hasil ekstrasi

3.5.6 Skenario Perancangan & Pengujian Sistem
Skenario pengujian sistem dirancang untuk mengevaluasi kinerja secara end-to-end, mulai dari masukan berupa citra struk pembelian hingga keluaran berupa data yang tertulis di Google Sheets. Evaluasi dilakukan dalam dua tahap utama: evaluasi kualitas ekstraksi informasi dan evaluasi kinerja orkestrasi agent. Pada setiap tahap, perhitungan matematis dilakukan secara manual berdasarkan rumus yang telah didefinisikan pada Bab II untuk memverifikasi kebenaran implementasi metrik.

A. Skenario Fine-Tuning GLM-OCR dengan LoRA
Proses fine-tuning dilakukan menggunakan LLAMA Factory dengan konfigurasi LoRA pada model GLM-OCR 0,9B. Parameter LoRA yang digunakan mencakup rank r = 8, learning rate 1×10⁻⁴, dan target module = all (seluruh lapisan linear). Dengan dimensi model d = 896 (dimensi tersembunyi GLM-0.5B decoder), jumlah parameter yang dapat dilatih pada satu lapisan LoRA dapat dihitung sesuai dengan persamaan (2.5) dengan sebagai berikut.

Matriks dekomposisi low-rank terdiri dari A ∈ ℝ^(r×k) dan B ∈ ℝ^(d×r), di mana r = 8 dan d = k = 896. Jumlah parameter trainable per lapisan: $$ Parameter_{LoRA} = r \times k + d \times r $$ $$ = 8 \times 896 + 896 \times 8 $$ $$ = 14.336 \text{ parameter} $$

Sebagai perbandingan, full fine-tuning pada lapisan yang sama memerlukan d × k = 896 × 896 = 802.816 parameter. Rasio efisiensi parameter LoRA terhadap full fine-tuning pada satu lapisan adalah: $$ Rasio = 14.336 / 802.816 \approx 0,0179 \approx 1,79 $$

Efisiensi ini menunjukkan bahwa LoRA hanya memodifikasi sekitar 1,79% parameter per lapisan dibandingkan full fine-tuning, yang memungkinkan pelatihan pada perangkat dengan memori GPU terbatas (≥ 8 GB VRAM).

Total dataset terdiri 885 pasangan citra-label 793 untuk training dan 92 untuk testing (90% : 10%), yang dikumpulkan dari delapan sumber dataset. Pelatihan dilakukan selama 5 epoch dengan batch size efektif 16

Page 114
<page_number>96</page_number>

(per_device_batch_size = 4 × gradient_accumulation_steps = 4) menggunakan cosine learning rate scheduler dengan warmup ratio 0,0001.

B. Skenario Evaluasi Kualitas Ekstraksi

Evaluasi kualitas ekstraksi dilakukan secara kuantitatif menggunakan tiga metrik utama: KIEval, ANLS*, dan Digit Accuracy. Kedua metrik ini dipilih karena saling melengkapi, KIEval mengukur ketepatan pada level pasangan entitas secara diskrit, sedangkan ANLS* mengukur kemiripan karakter secara kontinu sehingga lebih toleran terhadap kesalahan penulisan minor, dan digit accuracy dengan menormalisasikan kolom nilai harga untuk membandingkan kemiripan suatu harga tanpa tanda koma, titik, ataupun karakter diluar angka melalui exact match. Untuk keperluan verifikasi dan transparansi, berikut disajikan perhitungan manual dari kedua metrik menggunakan contoh ilustrasi pada Gambar 3.17.

<img>Receipt and tables showing ground-truth and prediction for OCR evaluation</img>

Gambar 3.19 Contoh ilustrasi ground-truth dan hasil prediksi GLM-OCR

B.1. Perhitungan Manual KIEval

KIEval mengevaluasi kualitas ekstraksi informasi kunci pada dua level sekaligus, yaitu level entitas (entity-level) dan level grup (group-level), dengan terlebih dahulu melakukan pencocokan struktural antar grup sebelum menghitung statistik evaluasi. Berbeda dengan Entity F1 konvensional yang mengevaluasi setiap pasangan (key, value) secara independen, KIEval mempertimbangkan relasi kontekstual antar entitas dalam satu grup yang sama. Berdasarkan skema ekstraksi pada Gambar 3.17, struktur data diklasifikasikan menjadi dua jenis grup sebagai berikut.

Tabel 3.4 Struktur grup ground-truth dan prediksi

Jenis Grup	ID Grup	Entitas yang Dievaluasi
Non-grup (payment)	Grup 0	payment.total_items, payment.grand_total, payment.tendered
Grup items	Grup 1	items.name, items.quantity, items.total_price (baris 1)
Grup items	Grup 2	items.name, items.quantity, items.total_price (baris 2)
Grup items	Grup 3	items.name, items.quantity, items.total_price (baris 3)
Sesuai definisi KIEval, entitas non-grup (payment) dimasukkan ke dalam Grup 0 sebagai grup khusus, sementara setiap baris items diperlakukan sebagai satu unit grup tersendiri.

B.1.1 Hungarian Matching Antar Grup

Sebelum menghitung statistik evaluasi, dilakukan pencocokan (matching) antara grup prediksi dan grup ground-truth menggunakan algoritma Hungarian. Skor pencocokan S(n,m) dihitung sebagai jumlah entitas yang identik antara grup prediksi ke-n dan grup ground-truth ke-m.

Tabel 3.5 Matriks Skor Pencocokan S(n,m) untuk Grup Items

GT Grup 1 (AYA)	GT Grup 2 (COTO)	GT Grup 3 (MILK)
Pred Grup 1 (AYAM)	2	0	0
Pred Grup 2 (COTO)	0	3	0
Pred Grup 3 (MILK)	0	0	2
Hasil Hungarian matching menghasilkan pasangan optimal sebagai berikut.

Tabel 3.6 Hasil pasangan grup setelah Hungarian Matching

Pasangan G	Grup Prediksi	Grup Ground-Truth	Keterangan
(n₀, m₀)	payment (Pred)	payment (GT)	Non-grup
(n₁, m₁)	items baris 1 (AYAM)	items baris 1 (AYA)	Grup items
(n₂, m₂)	items baris 2 (COTO)	items baris 2 (COTO)	Grup items
(n₃, m₃)	items baris 3 (MILK)	items baris 3 (MILK)	Grup items
B.1.2 Perhitungan KIEval Entity F1

KIEval Entity F1 menghitung statistik TP, FN, dan FP pada level entitas dalam konteks grup yang sudah dipasangkan. Setiap entitas dievaluasi menggunakan exact match di dalam grup yang telah dicocokkan.

Tabel 3.7 Perhitungan TP, FP, FN per setiap pasangan grup

Pasangan Grup	Entitas	GT	Prediksi	Se(n,m)	TP	FP	FN
(n₀, m₀) payment	total_items	7	7	1	1	0	0
grand_total	29.500	29.500	1	1	0	0
tendered	29.500	29.500	1	1	0	0

Tabel 3.8 Perhitungan TP, FP, FN per setiap pasangan grup (Lanjutan)

Pasangan Grup	Entitas	GT	Prediksi	Se(n,m)	TP	FP	FN
(n1, m1)
items
baris 1	item_name	INDOMIE
KALDU
AYA	INDOMIE
KALDU
AYAM	0	0	1	1
quantity	2	2	1	1	0	0
total_price	7.000	7.000	1	1	0	0
(n2, m2)
items
baris 2	item_name	INDOMIE
RASA
COTO	INDOMIE
RASA
COTO	1	1	0	0
quantity	4	4	1	1	0	0
total_price	14.000	14.000	1	1	0	0
(n3, m3)
items
baris 3	item_name	ULTRA
MILK
LOW FA	ULTRA
MILK
LOW FA	1	1	0	0
quantity	1	1	1	1	0	0
total_price	8.500	8.600	0	0	1	1
Akumulasi statistik keseluruhan: TPentity = 10, FPentity = 2, FNentity = 2 Nilai Precision, Recall, dan KIEval Entity F1 dapat dihitung sesuai persamaan (2.16)–(2.18) sebagai berikut.

Precision = $\frac{10}{10+2} = \frac{10}{12} \approx 0,833$

Recall = $\frac{10}{10+2} = \frac{10}{12} \approx 0,833$

KIEvalEntityF1 = $\frac{2 \times 0,833 \times 0,833}{0,833 + 0,833} = 0,833$

Hasil perhitungan menunjukkan bahwa KIEval Entity F1 memberikan menghasilkan nilai sebesar 0,833, yang mencerminkan bahwa dari 12 entitas yang dievaluasi, terdapat 2 kesalahan, yaitu halusinasi karakter pada nama produk

pertama (INDOMIE KALDU AYAM vs INDOMIE KALDU AYA) dan kesalahan digit pada harga item ketiga (8.600 vs 8.500).

B.2. Perhitungan Manual ANLS* ANLS* mengevaluasi kualitas ekstraksi informasi kunci dengan mengukur kemiripan karakter secara kontinu menggunakan Normalized Levenshtein Similarity (NLS). Berbeda dengan KIEval yang menggunakan exact match, ANLS* memberikan nilai parsial untuk prediksi yang hampir benar sehingga lebih toleran terhadap kesalahan penulisan minor akibat proses OCR. Metrik ini mendukung tipe data String, List, Dict, Tuple, dan None secara rekursif, sehingga mampu mengevaluasi struktur bersarang (nested) secara menyeluruh. Secara formal, ANLS* sesuai dengan persamaan (2.26).

Berdasarkan contoh pada Gambar 3.17, struktur data yang dievaluasi direpresentasikan sebagai pohon hierarki dapat digambarkan pada Gambar 3.18 sebagai berikut.

<img>Diagram of a tree structure representing data hierarchy. The root node is "Dict". It has two children: "payment Dict" and "items List". The "payment Dict" node has three children: "7", "29.500", and "29.500". The "items List" node has three children: "Dict", "Dict", and "Dict". The first "Dict" node has two children: "INDOMIE KALDU AYA" and "2". The second "Dict" node has two children: "7.000" and "INDOMIE RASA COTO". The third "Dict" node has two children: "4", "14.000", "ULTRA MILK LOW FA", "1", and "8.500".</img>

Gambar 3.20 Struktur pohon hierarki dari contoh ilustrasi Gambar 3.17

B.2.1 Dekomposisi Struktur dan Tipe Data

Sebelum menghitung skor, setiap nilai dalam ground-truth dan prediksi dipetakan ke tipe data yang sesuai dalam ANLS*.

Tabel 3.8 Pemetaan tipe data ANLS pada struktur evaluasi*

Node	Tipe ANLS*	Deskripsi
Top-level output	Dict	Memiliki beberapa kunci tetap
items	List of Dicts	Urutan tidak penting, semua elemen harus ada
Setiap baris item	Dict	Terdiri dari pasangan kunci-nilai tetap
item_name, quantity, total_price	String	Nilai teks yang dibandingkan karakter per karakter
payment	Dict	Kunci tetap tanpa urutan
total_items, grand_total, tendered	String	Nilai teks yang dibandingkan karakter per karakter
B.2.2 Hungarian Matching Pada Level List

Karena items bertipe List, ANLS* menggunakan algoritma Hungarian untuk menentukan pasangan optimal antara setiap elemen ground-truth dan prediksi berdasarkan skor ANLS* pairwise. Skor ANLS* pairwise dihitung terlebih dahulu untuk setiap kombinasi pasangan Dict item.

Tabel 3.9 Matriks skor ANLS pairwise antar item*

Pred Baris 1 (AYAM)	Pred Baris 2 (COTO)	Pred Baris 3 (MILK)
GT Baris 1 (AYA)	0,981	0,222	0,200
GT Baris 2 (COTO)	0,222	1,000	0,167
GT Baris 3 (MILK)	0,200	0,167	0,933
Page 120
<page_number>102</page_number>

Hasil Hungarian matching memilih pasangan dengan jumlah skor tertinggi, yaitu diagonal utama dengan total skor 0,981 + 1,000 + 0,933 = 2,914. Pasangan yang terbentuk adalah GT Baris 1 dengan Pred Baris 1, GT Baris 2 dengan Pred Baris 2, dan GT Baris 3 dengan Pred Baris 3. Tidak terdapat elemen yang tidak tercocokkan (unmatched) karena jumlah elemen GT dan prediksi sama.

B.2.3 Perhitungan NLS per Field String

Untuk setiap pasangan yang sudah dicocokkan, skor s pada level String dihitung menggunakan rumus sesuai persamaan (2.27) berikut.

$$ s(g, p) = \begin{cases} 1,0 - \frac{LD(g, p)}{max(|g|, |p|)} & \text{ jika NLS } \ge \tau \ 0,0 & \text{ jika NLS } < \tau \end{cases} $$

Dengan $\tau = 0,5$ sebagai ambang batas, dan LD adalah Levenshtein Distance.

Tabel 3.10 Perhitungan NLS per field pada setiap pasangan yang dicocokkan

Pasangan	Field	LD	max (|g|, |p|)	NLS	≥ τ?	s
Baris 1	item_name	1	18	0,944	Ya	0,944
quantity	0	1	1,000	Ya	1,000
total_price	0	5	1,000	Ya	1,000
Baris 2	item_name	0	18	1,000	Ya	1,000
quantity	0	1	1,000	Ya	1,000
total_price	0	6	1,000	Ya	1,000
Baris 3	item_name	0	17	1,000	Ya	1,000
quantity	0	1	1,000	Ya	1,000
total_price	1	5	0,800	Ya	0,800
payment	total_items	0	1	1,000	Ya	1,000
grand_total	0	6	1,000	Ya	1,000
tendered	0	6	1,000	Ya	1,000
Catatan pada field item_name baris 1: "INDOMIE KALDU AYA" memiliki 17 karakter dan "INDOMIE KALDU AYAM" memiliki 18 karakter. LD = 1 karena hanya terdapat satu penyisipan karakter 'M' di akhir string. Nilai NLS = 1 - 1/18 ≈

0,944 masih berada di atas ambang batas τ = 0,5, sehingga mendapat skor parsial dan tidak dinolkan.

B.2.4 Agregasi Skor s dan Panjang l

Skor s dan panjang l diagregasi secara rekursif dari level String ke atas hingga level top-level Dict.

Agregasi pada Level Dict per Baris Item: s(baris 1) = 0,944 + 1,000 + 1,000 = 2,944 ; l(baris 1) = 3 s(baris 2) = 1,000 + 1,000 + 1,000 = 3,000 ; l(baris 2) = 3 s(baris 3) = 1,000 + 1,000 + 0,800 = 2,800 ; l(baris 3) = 3

Agregasi pada Level List items: Karena tidak terdapat elemen yang tidak tercocokkan (unmatched), suku penalti bernilai nol. s(items) = 2,944 + 3,000 + 2,800 = 8,744 ; l(items) = 3 + 3 + 3 = 9

Agregasi pada Level Dict payment: s(payment) = 1,000 + 1,000 + 1,000 = 3,000 ; l(payment) = 3

Agregasi pada Level Top-Level Dict: stotal = s(items) + s(payment) = 8,744 + 3,000 = 11,744 ltotal = l(items) + l(payment) = 9 + 3 = 12

B.2.5 Perhitungan ANLS Final*

ANLS* =	stotal	=	11,744	≈ 0,979
ltotal		12	
Hasil perhitungan sesuai rumus (2.26) menunjukkan bahwa model memperoleh nilai ANLS* sebesar 0,979 (97,9%). Nilai ini lebih tinggi dibandingkan KIEval Entity F1 (0,833) karena ANLS* memberikan skor parsial pada field yang hampir benar. Secara khusus, kesalahan pada item_name baris 1 (AYAM vs AYA) tidak dinolkan melainkan mendapat skor 0,944, dan kesalahan digit pada total_price baris 3 (8.600 vs 8.500) mendapat skor 0,800. Kedua kondisi ini masih berada di atas ambang batas τ = 0,5 , sehingga skor parsial tetap diberikan. Hal ini mencerminkan karakteristik ANLS* yang lebih toleran terhadap kesalahan minor akibat proses OCR pada model kecil seperti GLM-OCR 0.9B. Rangkuman hasil perhitungan ANSL* dapat dilihat pada Tabel 3.11.

Tabel 3.11 Rekapitulasi kontribusi setiap komponen terhadap ANLS*

Komponen	s	l	Kontribusi ANLS*
items baris 1 (AYA vs AYAM)	2,944	3	0,981
items baris 2 (semua benar)	3,000	3	1,000
items baris 3 (8.500 vs 8.600)	2,800	3	0,933
payment (semua benar)	3,000	3	1,000
Total	11,744	12	0,979
B.3. Perhitungan Manual Digit Accuracy

Metrik KIEVal dan ANLS* belum cukup untuk mengevaluasi keakuratan numerik pada field harga. Sehingga dibutuhkan digit accuracy. Field harga yang dievaluasi dalam metrik digit accuracy dirangkum pada Tabel 3.12 berikut.

Tabel 3.12 Field harga evaluasi digit accuracy

Kategori	Field	Keterangan
items	unit_price	Harga satuan per item
items	discount_price	Potongan harga dalam nominal
items	total_price	Total harga per baris item
returned_items	unit_price	Harga satuan pada item yang dikembalikan
returned_items	total_refund	Total nilai refund
payment	subtotal_price	Subtotal sebelum pajak dan diskon
payment	grand_total	Total akhir yang harus dibayar
payment	tendered	Uang yang diserahkan oleh pelanggan
payment	change	Kembalian yang diterima pelanggan
payment	rounding	Nilai pembulatan
payment.discounts	amount	Nilai nominal diskon pada level pembayaran
payment.taxes	amount	Nilai nominal pajak
payment.additional_charges	amount	Biaya tambahan seperti biaya layanan
Misalnya diberikan satu sampel struk pembelian dari supermarket dengan ground truth dan prediksi model sebagaimana berikut. Contoh ini sengaja dirancang untuk memperlihatkan kasus di mana ANLS* menghasilkan skor tinggi namun digit accuracy memberikan penalti, sebagaimana motivasi awal metrik ini.

Ground Truth (GT)	Prediksi Model (PR)
items:	items:
index	unit_price	total_price	index	unit_price	total_price
0	12.500	25.000	0	12.500	25,000
1	9.000	9.000	1	2.000	9.000
payment:	payment:
subtotal_price	=	34.000	subtotal_price	=	34.000
grand_total	=	34.000	grand_total	=	34.500
tendered	=	50.000	tendered	=	50.000
change	=	16.000	change	=	16.000
Catatan: Nilai ditampilkan dalam format desimal dengan pemisah ribuan (.,).

Gambar 3.21 Perbandingan ground truth dan prediksi model Aplikasi fungsi normalisasi d(·) pada seluruh field yang tidak kosong.

Tabel 3.13 Perbandingan hasil normalisasi

Field	d(v*)	d(v)	Cocok
items[0].unit_price	12500	12500	Ya
items[0].total_price	25000	25000	Ya
items[1].unit_price	9000	2000	Tidak
items[1].total_price	9000	9000	Ya
payment.subtotal_price	34000	34000	Ya
payment.grand_total	34000	34500	Tidak
payment.tendered	50000	50000	Ya
payment.change	16000	16000	Ya
Kemudian akumulasi statistik. Total field yang dievaluasi (|F| dengan d(v*) ≠ Ø) = 8. Total field yang cocok secara digit = 6. Kemudian perhitungan Digit Accuracy pada sampel tunggal ini sebagai berikut. DA = $\frac{6}{8} \times 100% = 75,00%$

Perbandingan dengan skor ANLS* pada field yang sama. Perlu dicatat bahwa items[1].unit_price dengan prediksi "2.000" versus ground truth "9.000" menghasilkan LD = 1, sehingga NLS = 1/5 = 0,20 dan skor ANLS* parsial = 0,80. Dengan kata lain, ANLS* masih memberikan kredit parsial sebesar 0,80 pada prediksi yang secara makna numerik sama sekali berbeda nilainya. Sedangkan jika dihitung menggunakan KIEVal Entity F1 ground truth items[0].total_price = "25.000" dan prediksi "25,000" akan dihitung salah, dengan digit accuracy melalui normalisasinya mengatasi itu, karena variasi format yang disebabkan oleh faktor seperti kualitas pencahayaan atau noise pada citra struk GLM-OCR bisa saja salah menangkap titik atau koma pada foto struk, sehingga dengan digit accuracy menjadi "25000" dimana hasilnya akan bernilai benar.