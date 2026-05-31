Peningkatan Keterbacaan Teks Pada Citra Struk
Pembayaran Menggunakan Segmentasi OTSU
Alwi Andika Panggabean1), Fitra Hidayat Lubis2), Rafif Risdi Aulia3),
Muhammad Haikal Akmal4) , M. Khalil Gibran5)
1,2,3,4,5)Prodi Ilmu Komputer , Fakultas Sains dan Teknologi,
Universitas Islam Negeri Sumatera Utara, Indonesia
Abstrak
Citra struk pembayaran sering mengalami penurunan kualitas akibat pencahayaan buruk, penuaan
kertas, atau noise pemindaian, yang mengganggu keterbacaan teks dan digitalisasi data. Penelitian
ini menggunakan metode segmentasi Otsu untuk meningkatkan keterbacaan dengan memisahkan
area teks dan latar belakang secara optimal. Prosesnya mencakup akuisisi citra, pra-pemrosesan,
segmentasi, dan evaluasi menggunakan rasio akurasi OCR dan kontras citra. Hasilnya menunjukkan
peningkatan signifikan dalam keterbacaan dan akurasi ekstraksi data, sehingga mendukung
pengembangan sistem digitalisasi dokumen berbasis citra.
Kata Kunci: Citra, Otsu, Struk.
Abstract
Receipt images often experience quality degradation due to poor lighting, paper aging, or scanning
noise, which affects text readability and hinders data digitization. This study applies the Otsu
segmentation method to improve readability by optimally separating text areas from the background.
The process includes image acquisition, preprocessing, segmentation, and evaluation using OCR
accuracy ratio and image contrast. The results show a significant improvement in readability and data
extraction accuracy, supporting the development of image-based document digitization systems.
Keywords: Image, Otsu, Receipt
Device : Journal Of Information System, Computer Science And Information Technology | 155
Vol. 6 No. 1 Juni 2025 Hal : 155 - 164 E-ISSN: 2723-1089
P-ISSN: 2776-7779
PENDAHULUAN
Struk pembayaran merupakan dokumen penting yang digunakan sebagai
bukti transaksi dalam berbagai sektor, seperti perdagangan, perbankan, dan
administrasi (Rahmawati et al., 2025). Seiring berjalannya waktu, kualitas cetakan
pada struk pembayaran cenderung menurun akibat faktor-faktor seperti kertas
yang mudah pudar, kerusakan fisik, hingga kualitas cetak yang rendah. Kondisi ini
menyebabkan keterbacaan teks menjadi menurun, sehingga menyulitkan dalam
proses digitalisasi dan ekstraksi informasi menggunakan sistem berbasis OCR
(Optical Character Recognition) (Alhakim, 2024).
Dalam upaya meningkatkan keterbacaan teks pada citra struk, diperlukan
metode pemrosesan citra yang efektif untuk memisahkan teks dari latar belakang.
Salah satu pendekatan yang banyak digunakan adalah segmentasi citra. Segmentasi
Otsu merupakan metode thresholding yang otomatis mencari nilai ambang batas
terbaik untuk membedakan objek dan latar belakang dengan memaksimalkan
varians antar kelas piksel.
Manusia merupakan makhluk visual dengan mengandalkan mata untuk
mengetahui dunia sekelilingnya. Mata manusia mampu menggambarkan objek
untuk mendapatkan sebuah informasi, cahaya dan bayangan dapat mempengaruhi
sebuah objek dalam dunia nyata (Sari et al., 2020).
Penelitian ini bertujuan untuk menerapkan metode segmentasi Otsu dalam
meningkatkan keterbacaan teks pada citra struk pembayaran. Diharapkan, hasil
segmentasi yang optimal dapat memperbaiki hasil pembacaan OCR dan mendukung
proses digitalisasi dokumen secara lebih akurat
METODE PENELITIAN
Untuk mengidentifikasi permasalahan yang ditemukan, digunakan metode
penelitian. Selanjutnya, dilakukan analisis terhadap permasalahan tersebut untuk
kemudian menemukan solusi yang tepat guna menyelesaikannya. Penelitian ini
dilakukan melalui beberapa tahap:
Device : Journal Of Information System, Computer Science And Information Technology | 156
Vol. 6 No. 1 Juni 2025 Hal : 155 - 164 E-ISSN: 2723-1089
P-ISSN: 2776-7779
ORC
Optical Character Recognition (OCR) adalah teknologi yang digunakan untuk
mengubah gambar berisi teks menjadi teks yang dapat diproses oleh komputer.
Awalnya, teknologi ini hanya mampu mengenali karakter satu per satu dengan jenis
huruf yang seragam (Wijaya & Lubis, 2022). OCR merupakan teknologi yang mampu
mengubah karakter dalam gambar menjadi teks yang dapat diedit dan dicari
(Poudel et al., 2023).
Akuisisi Data
Data berupa citra struk pembayaran diperoleh dari hasil pemindaian atau
dokumentasi menggunakan kamera smartphone. Beragam kondisi pencahayaan
dan kualitas cetak sengaja dipertahankan untuk menguji keandalan metode.
Data dikumpulkan dari struk belanja kemudian diolah dan dipreprocessing
sebelum dilakukan proses analisis. Data yang digunakan terdiri dari foto struk
belanja yang telah diambil
Pra Pemprosesan
Pra-pemrosesan dilakukan untuk meningkatkan kualitas citra sebelum
segmentasi. Tahapan pra-pemrosesan meliputi:
a. Grayscale Conversion
Gambar skala abu-abu terdiri dari berbagai tingkat kegelapan, dari hitam
pekat hingga putih terang. Sederhananya, gambar ini terdiri dari warna hitam, putih,
dan berbagai corak abu-abu, dengan berbagai tingkat kecerahan abu-abu. Dalam
gambar skala abu-abu, nilai setiap piksel bergantung pada jumlah bit data yang
digunakan untuk merepresentasikannya (Sari et al., 2020).
Pada citra grayscale, terdapat 256 tingkat warna, karena citra ini
menggunakan 8 bit untuk merepresentasikan setiap piksel. Nilai intensitas piksel
dalam citra grayscale berada dalam rentang 0 hingga 255, sehingga tidak akan
melebihi 255 atau kurang dari 0. Notasi (x, y) menunjukkan posisi piksel, sedangkan
nilai intensitasnya mewakili seberapa terang atau gelap piksel tersebut, Misalnya,
jika sebuah citra memiliki ukuran lebar 512 piksel dan tinggi 512 piksel, maka
Device : Journal Of Information System, Computer Science And Information Technology | 157
Vol. 6 No. 1 Juni 2025 Hal : 155 - 164 E-ISSN: 2723-1089
P-ISSN: 2776-7779
jumlah bit yang diperlukan untuk menyimpan seluruh citra dapat dihitung
berdasarkan ukuran tersebut.
Gambar 1.1 Perbandingan Gradasi Warna
b. Noise Removal
Noise (derau) merupakan gangguan berupa piksel acak yang menurunkan
kualitas suatu citra. Keberadaan noise perlu dikurangi atau dihilangkan karena
dapat menghambat proses pengambilan informasi dari citra tersebut. Citra yang
diperoleh sering kali memiliki kualitas rendah, yang bisa disebabkan oleh faktor
teknis, keterbatasan perangkat, atau pencahayaan yang tidak memadai. Untuk
mengatasi permasalahan ini, diperlukan teknik pemrosesan citra guna memperoleh
hasil citra yang lebih optimal dan sesuai kebutuhan (Fachrunnisa et al., 2024).
c. Normalization
Normalisasi adalah cara menyusun data dalam sebuah database agar tidak ada
data yang berulang-ulang dan supaya lebih rapi. Dengan normalisasi, data jadi lebih
mudah diatur, dicari, dan digunakan. Proses ini biasanya dilakukan dengan
memecah data ke dalam beberapa tabel, lalu menghubungkannya sesuai aturan
tertentu agar data tetap aman dan fleksibel untuk diolah (Nurjihan et al., 2024).
Segmentasi Otsu
Metode Otsu pertama kali diperkenalkan oleh Nobuyuki Otsu pada tahun
1996. Teknik ini secara otomatis menentukan nilai ambang batas (threshold) untuk
mengubah gambar berwarna abu-abu (grayscale) menjadi gambar hitam putih
Device : Journal Of Information System, Computer Science And Information Technology | 158
Vol. 6 No. 1 Juni 2025 Hal : 155 - 164 E-ISSN: 2723-1089
P-ISSN: 2776-7779
(biner), dengan cara membandingkan nilai ambang tersebut dengan nilai tiap piksel
pada gambar (Sarimuddin et al., 2024).
Dengan metode ambang Otsu, kita bisa membagi gambar menjadi beberapa
bagian secara akurat menggunakan informasi kecerahan dari histogram grayscale.
Teknik thresholding ini memanfaatkan perbedaan tingkat terang dan gelap untuk
memisahkan objek dari latar belakang (Rosnelly et al., 2024). Gibran et al. (2020)
menunjukkan bahwa kualitas segmentasi citra sangat mempengaruhi keberhasilan
proses pengenalan objek (dalam hal ini wajah) menggunakan metode LVQ.
Segmentasi dilakukan dengan pendekatan Fuzzy C-Means dan K-Means yang
terbukti meningkatkan akurasi pengenalan. Hal ini menguatkan bahwa metode
segmentasi seperti Otsu pun dapat digunakan secara efektif untuk memisahkan
objek penting dari latar belakang citra buram sebelum dilakukan proses analisis
lanjutan seperti OCR.
HASIL DAN PEMBAHASAN
Citra Struk Pembayaran Awal
Pada tahap ini, citra struk pembayaran yang diambil menggunakan kamera
atau hasil scan ditampilkan. Citra awal menunjukkan beberapa permasalahan
umum seperti noise, pencahayaan yang tidak merata, dan kontras teks yang rendah
terhadap latar belakang.
Gambar 1.2 Struk pembayaran awal 1
Device : Journal Of Information System, Computer Science And Information Technology | 159
Vol. 6 No. 1 Juni 2025 Hal : 155 - 164 E-ISSN: 2723-1089
P-ISSN: 2776-7779
Gambar 1.3 Struk pembayaran awal 2
Konversi Grayscale
Tahap pertama yang dilakukan setelah mendapatkan citra struk pembayaran
adalah konversi citra dari berwarna menjadi grayscale. Proses ini penting untuk
menyederhanakan informasi dalam citra dengan hanya mempertahankan intensitas
kecerahan piksel tanpa memperhitungkan warna. Dengan citra grayscale, sistem
dapat lebih fokus pada perbedaan terang dan gelap antara teks dan latar belakang,
sehingga memudahkan proses segmentasi selanjutnya.
Pada citra grayscale, nilai intensitas piksel berada dalam rentang 0 (hitam)
hingga 255 (putih). Dengan hanya menggunakan satu kanal warna, ukuran file citra
menjadi lebih kecil dan komputasi lebih ringan. Hasil konversi ini diharapkan dapat
meningkatkan kontras teks terhadap latar belakang, sehingga tahap segmentasi dan
ekstraksi informasi menjadi lebih akurat (Aaisyah & Putri, 2025).
Penerapan Segmentasi Otsu
Setelah citra dikonversi ke dalam bentuk grayscale, langkah berikutnya adalah
penerapan metode segmentasi Otsu. Metode ini bekerja dengan menganalisis
histogram intensitas piksel untuk menemukan nilai ambang batas optimal yang
membedakan objek (teks) dari latar belakang. Otsu memilih nilai threshold yang
memaksimalkan perbedaan antara kedua kelas piksel, sehingga menghasilkan
segmentasi yang lebih efektif tanpa perlu penyesuaian manual (Zheng et al., 2022).
Device : Journal Of Information System, Computer Science And Information Technology | 160
Vol. 6 No. 1 Juni 2025 Hal : 155 - 164 E-ISSN: 2723-1089
P-ISSN: 2776-7779
Hasil segmentasi Otsu mengubah citra grayscale menjadi citra biner, di mana
teks tampil sebagai piksel berwarna hitam di atas latar belakang putih. Proses ini
sangat membantu dalam memperjelas teks yang sebelumnya sulit terbaca akibat
gangguan noise atau ketidakmerataan pencahayaan. Dengan segmentasi yang baik,
persiapan untuk tahap ekstraksi teks dapat dilakukan dengan hasil yang lebih
optimal (Ackar et al., 2019).
Ekstraksi Teks Menggunakan OCR
Tahap selanjutnya setelah segmentasi adalah ekstraksi teks menggunakan
metode Optical Character Recognition (OCR). OCR berfungsi untuk mengenali
karakter-karakter dalam citra biner dan mengubahnya menjadi teks digital. Dengan
latar belakang yang bersih dan teks yang lebih tajam setelah segmentasi, sistem OCR
dapat bekerja lebih efektif dan menghasilkan tingkat akurasi yang lebih tinggi dalam
membaca teks(Angela et al., 2024).
Proses ekstraksi ini sangat penting dalam upaya digitalisasi dokumen, karena
memungkinkan data yang sebelumnya hanya tersedia dalam bentuk cetak menjadi
mudah disimpan, dicari, dan dianalisis. Dengan dukungan pra-pemrosesan dan
segmentasi yang tepat, hasil dari OCR dapat digunakan untuk berbagai keperluan,
seperti pelaporan transaksi, rekap data belanja, hingga integrasi ke sistem database
(Fadjeri, 2024).
Gambar 3.1 Hasil dari OCR Pada Struk pertama
Device : Journal Of Information System, Computer Science And Information Technology | 161
Vol. 6 No. 1 Juni 2025 Hal : 155 - 164 E-ISSN: 2723-1089
P-ISSN: 2776-7779
Gambar 3.2 Hasil dari OCR Pada Struk Kedua
SIMPULAN
Berdasarkan hasil pengujian aplikasi segmentasi citra struk menggunakan
metode Otsu, dapat disimpulkan bahwa metode ini mampu meningkatkan
keterbacaan teks secara visual dengan memisahkan teks dari latar belakang secara
cukup baik, terutama pada gambar struk yang memiliki kontras tinggi dan
pencahayaan merata. Namun demikian, hasil pengenalan teks menggunakan Optical
Character Recognition (OCR) menunjukkan bahwa akurasi pembacaan masih
rendah. Hal ini terlihat dari banyaknya karakter yang keliru terbaca, seperti huruf
dan angka yang tertukar, serta munculnya karakter asing yang tidak relevan dengan
isi struk.
Struk yang memiliki pencahayaan tidak merata, teks kecil, atau kondisi buram
menghasilkan output OCR yang buruk meskipun telah melalui proses binarisasi
dengan Otsu. Bahkan pada beberapa bagian, teks yang sebenarnya masih terbaca
oleh mata manusia tidak dapat dikenali dengan benar oleh sistem. Ini menunjukkan
bahwa meskipun metode Otsu cukup efektif untuk segmentasi awal, ia belum cukup
kuat untuk mendukung akurasi OCR secara langsung, terutama pada citra struk
yang diambil dalam kondisi nyata.
Dengan demikian, meskipun segmentasi Otsu memberikan peningkatan
keterbacaan visual, dibutuhkan langkah tambahan seperti peningkatan kualitas
Device : Journal Of Information System, Computer Science And Information Technology | 162
Vol. 6 No. 1 Juni 2025 Hal : 155 - 164 E-ISSN: 2723-1089
P-ISSN: 2776-7779
citra, segmentasi berbasis lokal (misalnya adaptive thresholding), atau pembatasan
area pembacaan (ROI) agar hasil pembacaan OCR menjadi lebih akurat dan dapat
diterapkan secara lebih luas dalam digitalisasi dokumen struk. Metode Otsu tetap
relevan sebagai langkah awal segmentasi, namun perlu dikombinasikan dengan
teknik pendukung lainnya untuk mencapai hasil optimal.
DAFTAR PUSTAKA
[1] Aaisyah, D., & Putri, S. (2025). Implementation of Grayscale Image Transformation and
Histogram Equalization Methods in Digital Image Processing. Krisnadana (Jurnal Komputer,
Sistem Kendali & Jaringan), 4(2), 111–121.
[2] Ackar, H., Almisreb, A. A., & Saleh, M. A. (2019). A Review on Image Enhancement Techniques.
Southeast Europe Journal of Soft Computing, 8(1).
https://doi.org/10.21533/scjournal.v8i1.175
[3] Alhakim. (2024). SEKOLAH MENGGUNAKAN TEKNOLOGI OPTICAL CHARACTER
RECOGNITION ( OCR ) TESSERACT DENGAN METODE EXTREME PROGRAMMING ( Studi
Kasus : MA NASY ’ ATUL KHAIR - DEPOK ) Oleh : Muhammad Daffa Alhakim. V–136.
[4] Angela, S. M., Eviyanti, A., & Mauliana, M. I. (2024). Pengembangan teknologi optical character
recognition di flutter berupa deteksi teks pada gambar. Jurnal TEKINKOM, 7, 17–24.
https://doi.org/10.37600/tekinkom.v7i1.1167
[5] Fachrunnisa, N., Ari Usman, & Mufida Khairani. (2024). Implementasi Noise Removal Dan
Image Enhancement Pada Citra Digital Menggunakan Metode Adaptive Median Filter. Jurnal
Ilmu Komputer Dan Sistem Informasi, 3(1), 11–20. https://doi.org/10.70340/jirsi.v3i1.95
[6] Fadjeri, A. (2024). Identifikasi Teks dari Citra Menggunakan Optical Character Recognition.
Jurnal Ilmiah SINUS, 22(2), 13. https://doi.org/10.30646/sinus.v22i2.819
[7] Gibran, M. K., Nababan, E. B., & Sihombing, P. (2020). Analysis of Face Recognition with Fuzzy
C-Means Clustering Image Segmentation and Learning Vector Quantization. MECnIT 2020 -
International Conference on Mechanical, Electronics, Computer, and Industrial Technology, 188–
193. https://doi.org/10.1109/MECnIT48290.2020.9166649
[8] Nurjihan, S. W., Faturrahman, N., & Wiguna, I. M. (2024). Pengenalan Pola Ekspresi Wajah
Untuk Pengolahan Citra Menggunakan Metode Convolutional Neural Network. Teknik
Informatika Dan Sistem Informasi, 11(4).
[9] Poudel, U., Regmi, A. M., Stamenkovic, Z., & Raja, S. P. (2023). Applicability of OCR Engines for
Text Recognition in Vehicle Number Plates, Receipts and Handwriting. Journal of Circuits,
Systems and Computers, 32(18). https://doi.org/10.1142/S0218126623503218
[10] Rahmawati, E. V., Nuur, M., Thoha, F., & Luhur, U. B. (2025). Tata Kelola Keuangan untuk
Meningkatkan Efektivitas dan Efisiensi Pelaku UMKM Desa Girikerto , Sleman , Daerah
Istimewa Yogyakarta ,. Jurnal Mutiara Ilmu Akuntansi, 3(April).
[11] Rosnelly, R., Wahyuni, L., & Hardianto, H. (2024). Pelatihan Pembelajaran Rancang Bangun
Aplikasi Metode Segmentasi Dengan Thresholding. Publikasi Pengadian Masyarakat, 4(1), 01–
10. https://doi.org/10.22303/publidimas.v4i1.345
[12] Sari, I. E. Y., Furqan, M., & Sriani, S. (2020). Penerapan Metode Otsu dalam Melakukan
Segmentasi Citra pada Citra Naskah Arab. MATRIK : Jurnal Manajemen, Teknik Informatika Dan
Rekayasa Komputer, 20(1), 59–72. https://doi.org/10.30812/matrik.v20i1.658
[13] Sarimuddin, S., Muchtar, M., Pasrun, Y. P., Hasidu, L. A. F., & Riska, R. (2024). Penentuan Tingkat
Kesehatan Komunitas Mangrove Secara Otomatis Menggunakan Otsu Thresholding. Jurnal
Informatika Dan Rekayasa Perangkat Lunak, 6(1), 30–39.
Device : Journal Of Information System, Computer Science And Information Technology | 163
Vol. 6 No. 1 Juni 2025 Hal : 155 - 164 E-ISSN: 2723-1089
P-ISSN: 2776-7779
[14] Wibawa, C., & Anggraeni, D. T. (2023). Comparison of Image Segmentation Method in Image
Character Extraction Preprocessing Using Optical Character Recoginiton. Jurnal Teknik
Informatika (Jutif), 4(3), 583–589. https://doi.org/10.52436/1.jutif.2023.4.3.956
[15] Wijaya, I., & Lubis, C. (2022). Pengimplementasian Ocr Menggunakan Cnn Untuk Ekstraksi
Teks Pada Gambar. Jurnal Ilmu Komputer Dan Sistem Informasi, 10(1).
https://doi.org/10.24912/jiksi.v10i1.17836
[16] Zheng, J., Gao, Y., Zhang, H., Lei, Y., & Zhang, J. (2022). OTSU Multi-Threshold Image
Segmentation Based on Improved Particle Swarm Algorithm. Applied Sciences (Switzerland),
12(22). https://doi.org/10.3390/app122211514