Page 1
SEMINAR PROPOSAL

OTOMATISASI ENTRI DATA STRUK PEMBELIAN MENGGUNAKAN VISION-LANGUAGE MODEL (VLM) DENGAN FINE-TUNING LORA SERTA ORKESTRASI MULTI-AGENT HIERARKIS BERBASIS MODEL CONTEXT PROTOCOL (MCP)

Diajukan Untuk Memenuhi Salah Satu Syarat Memperoleh Gelar Sarjana Teknik

<img>Universitas Halu Oleo Logo</img>

LA ODE MUHAMMAD YUDHY PRAYITNO E1E122064

JURUSAN INFORMATIKA FAKULTAS TEKNIK UNIVERSITAS HALU OLEO KENDARI 2026

Page 2
LEMBAR PENGESAHAN

SEMINAR PROPOSAL OTOMATISASI ENTRI DATA STRUK PEMBELIAN MENGGUNAKAN VISION-LANGUAGE MODEL (VLM) DENGAN FINE-TUNING LORA SERTA ORKESTRASI MULTI-AGENT HIERARKIS BERBASIS MODEL CONTEXT PROTOCOL (MCP)

Adalah benar dibuat oleh saya sendiri dan belum pernah dibuat dan diserahkan sebelumnya baik sebagian ataupun seluruhnya, baik oleh saya maupun orang lain, baik di Universitas Halu Oleo ataupun institusi pendidikan lainnya. Kendari, 2026

La Ode Muhammad Yudhy Prayitno E1E122064

Pembimbing I Pembimbing II

Prof. Dr. Ir. La Ode Muhammad Golok Jaya, S.T., M.T. NIP. 197610202005011002

Asa Hari Wibowo, S.T., M.Eng. NIP. 199408172022031014

Mengetahui, Ketua Jurusan Informatika Fakultas Teknik Universitas Halu Oleo

Isnawaty, S.Si., M.T. NIP. 197611172008122001

<page_number>ii</page_number>

Page 3
INTISARI
La Ode Muhammad Yudhy Prayitno, E1E122064

Otomatisasi Entri Data Struk Pembelian Menggunakan Vision-Language Model (VLM) dengan Fine-Tuning LoRA Serta Orkestrasi Multi-Agent Hierarkis Berbasis Model Context Protocol (MCP)

Proposal, Fakultas Teknik, 2026

Kata Kunci: Ekstraksi Informasi Kunci, Vision-Language Model, LoRA, Multi-Agent Hierarkis, Model Context Protocol

Proses entri data secara manual memiliki tingkat kesalahan yang berkisar antara 0,55% hingga 3,6% per field dan dan dapat mencapai 26,9% pada kondisi tertentu akibat faktor kelelahan serta distraksi operator manusia. Pendekatan berbasis Optical Character Recognition (OCR) tradisional tidak mampu memahami struktur semantik dokumen sehingga menghasilkan ekstraksi yang tidak akurat pada kondisi struk dengan kualitas gambar rendah atau format yang tidak konsisten. Penelitian ini mengusulkan sistem bernama Klaudia yang mengotomatisasi seluruh alur entri data struk pembelian secara end-to-end, mulai dari ekstraksi informasi kunci hingga pencatatan data ke dalam Google Sheets tanpa pengetikan ulang oleh pengguna.

Klaudia menggunakan model GLM-OCR 0,9 miliar parameter yang di-fine-tune dengan teknik Low-Rank Adaptation (LoRA). Orkestrasi alur kerja dilakukan melalui arsitektur Hierarchical Multi-Agent Teams menggunakan LangGraph, yang terdiri dari Supervisor Agent, SQL Agent, dan Data Entry Team, dengan MCP-SQLite dan MCP-GSheets sebagai batas eksekusi tool berbasis Model Context Protocol (MCP). Sistem dilengkapi dengan lapisan guardrails ganda menggunakan Llama Prompt Guard 2 dan mekanisme LLM-as-Judge, serta mekanisme Human-in-the-Loop (HITL). Kinerja sistem dievaluasi secara menggunakan metrik ekstraksi KIEval, ANLS*, dan Digit Accuracy, serta metrik agentic berupa AST accuracy dan Pass@K untuk mengukur keakuratan pemanggilan tool MCP oleh agent.

<page_number>iii</page_number>

Page 4
ABSTRACT

La Ode Muhammad Yudhy Prayitno, E1E122064

Automating Purchase Receipt Data Entry Using LoRA-Fine-Tuned Vision-Language Models (VLM) and Hierarchical Multi-Agent Orchestration Based on Model Context Protocol (MCP)

Proposal, Faculty of Engineering, 2026

Keyword: Key Information Extraction, Vision-Language Model, LoRA Fine-Tuning, Hierarchical Multi-Agent, Model Context Protocol

Manual data entry processes exhibit an error rate ranging from 0.55% to 3,6% per field and can reach up to 26.9% under certain conditions due to operator fatigue and distraction. Traditional Optical Character Recognition (OCR) approaches are unable to capture the semantic structure of documents, resulting in inaccurate extraction, particularly for receipts with low image quality or inconsistent formats. This study proposes a system named Klaudia that automates the entire receipt data entry pipeline end-to-end, from key information extraction to recording data into Google Sheets without requiring manual retyping by users.

Klaudia utilizes a GLM-OCR model with 0.9 billion parameters, fine-tuned using the Low-Rank Adaptation (LoRA) technique. Workflow orchestration is implemented through a Hierarchical Multi-Agent Teams architecture using LangGraph, consisting of a Supervisor Agent, SQL Agent, and Data Entry Team, with MCP-SQLite and MCP-GSheets serving as tool execution boundaries based on the Model Context Protocol (MCP). The system is equipped with dual-layer guardrails using Llama Prompt Guard 2 and an LLM-as-Judge mechanism, along with a Human-in-the-Loop (HITL) mechanism. System performance is evaluated using extraction metrics KIEval, ANLS*, and Digit Accuracy, as well as agentic metrics such as AST accuracy and Pass@K to measure the accuracy of MCP tool invocation by the agents.

<page_number>iv</page_number>

Page 5
DAFTAR ISI

LEMBAR PENGESAHAN .................................................................................. ii INTISARI........................................................................................................ iii ABSTRACT ................................................................................................... iv DAFTAR ISI ................................................................................................... v DAFTAR GAMBAR ...................................................................................... viii DAFTAR TABEL .......................................................................................... x BAB I PENDAHULUAN ................................................................................ 1 1.1 Latar Belakang ...................................................................................... 1 1.2 Rumusan Masalah ................................................................................ 5 1.3 Batasan Masalah .................................................................................. 5 1.4 Tujuan Penelitian .................................................................................. 5 1.5 Manfaat Penelitian ................................................................................ 6 1.6 Sistematika Penulisan Laporan .............................................................. 6 1.7 Tinjauan Pustaka .................................................................................. 7 BAB II LANDASAN TEORI ........................................................................... 15 2.1 Struk Pembelian .................................................................................. 15 2.2 Semi-Structured Data .......................................................................... 16 2.3 Data Entry .......................................................................................... 17 2.4 Large Language Models (LLM) ............................................................ 18 2.5 Transformers ...................................................................................... 19 2.6 Instruction Fine-Tuning dan Parameter-Efficient Fine-Tuning ............... 21 2.6.1 Instruction Fine-Tuning (IFT) .......................................................... 22 2.6.2 Low-Rank Adaptation (LoRA) ....................................................... 23 2.6.3 LLAMA Factory ............................................................................. 24 2.7 Vision Language Model (VLM) ............................................................. 25 2.8 Visual Document Understanding (VDU) ............................................... 27 2.8.1 OCR Tradisional ............................................................................ 27 2.8.2 VLM-Based Document Understanding ............................................ 28 2.8.3 General Language Model-OCR (GLM-OCR) ................................... 28

<page_number>v</page_number>

Page 6
2.9	Key Information Extraction	36
2.10	Agentic AI	36
2.10.1	AI Agent	37
2.10.2	Multi Agent System (MAS)	38
2.10.3	Hierarchical Agent Teams	39
2.11	HITL (Human in the Loop)	40
2.12	MCP (Model Context Protocol)	41
2.13	Prompt Engineering	42
2.13.1	Zero Shot Prompting	43
2.13.2	Few Shot Prompting	43
2.13.3	Chain of Thought Prompting	44
2.13.4	ReAct Prompting	44
2.13.5	Persona-based Prompting	44
2.14	Context Engineering	45
2.15	Benchmark Agentic AI	46
2.15.1	τ2-Bench	46
2.15.2	MCP-Atlas	46
2.15.3	APEX-Agents	47
2.15.4	MRCR v2	48
2.15.5	Komparasi Performa Model Berdasarkan Benchmark	49
2.16	Guardrails	50
2.16.1	Prompt Injection dan Jailbreaking	51
2.16.2	Blacklist Domain dengan LLM as Judge	52
2.17	Basis Data SQLite	54
2.18	Google Sheets	55
2.19	Evaluation Metrics	56
2.19.1	Key Information Extraction Evaluation (KIEval)	57
2.19.2	Average Normalized Levenshtein Similarity Star (ANLS*)	59
2.19.3	MCP Tool Accuracy	62
2.20	React Native dan Expo	66
2.21	Agile Scrum	66
<page_number>vi</page_number>

Page 7
2.22	Flowchart	68
2.23	Unified Modeling Language (UML)	69
2.24	Pengujian BlackBox	74
BAB III METODOLOGI PENELITIAN 68
3.1	Metode Pengumpulan Data	68
3.1.1	Akuisisi Dataset Publik (Open Source)	68
3.1.2	Pengumpulan Data Manual (Web Discovery)	69
3.1.3	Web Scraping (Pinterest)	70
3.1.4	Pengambilan Data Primer (Real-Life)	70
3.2	Metode Pengembangan Sistem	72
3.3	Waktu dan Tempat Penelitian	74
3.3.1	Waktu	74
3.3.2	Tempat Penelitian	75
3.4	Analisis Kebutuhan Sistem	75
3.4.1	Analisis Kebutuhan Fungsional	75
3.4.2	Analisis Kebutuhan Nonfungsional	77
3.5	Analisis Perancangan Sistem	79
3.5.1	Flowchart	79
3.5.2	Perancangan Unified Modeling Language (UML)	82
3.5.3	Perancangan Antarmuka	93
3.5.4	Spesifikasi Data	94
3.5.5	Skenario Perancangan & Pengujian Sistem	95
3.5.6	Pengujian Black Box	111
DAFTAR PUSTAKA 114
<page_number>vii</page_number>

Page 8
DAFTAR GAMBAR

Gambar 2.1 Arsitektur Transformer (Vaswani dkk., 2023)	20
Gambar 2.2 Ilustrasi reparameterisasi LoRA (Hu dkk., 2021)	24
Gambar 2.3 Arsitektur LLaMA Factory (Zheng dkk., 2024)	25
Gambar 2.4 Contoh arsitektur VLM (H. Liu dkk., 2023)	26
Gambar 2. 5 Performa GLM-OCR pada OmniDocBench V1.5 dibandingkan dengan model-model lain (Duan, S. dkk., 2026)	29
Gambar 2. 6 Arsitektur keseluruhan dan alur kerja kerangka GLM-OCR (Duan, S. dkk., 2026)	30
Gambar 2.7 Arsitektur model GLM-V (Hong, W. dkk., 2026)	31
Gambar 2.8 Arsitektur PP-DocLayoutV3 (Cui dkk., 2026)	33
Gambar 2.9 Contoh arsitektur hierarchical agent teams (W. Zhang dkk., 2026)	39
Gambar 2.10 Arsitektur HITL pada sistem Agentic AI berbasis LangGraph (LangChain, 2026)	41
Gambar 2.11 Overview sistem LLM-as-judge (H. Li dkk., 2024)	54
Gambar 3.1 Contoh gambar struk (a) Pinterest dan (b) CORD-v2	71
Gambar 3.2 Contoh gambar struk (c) Digital, (d) ExpressExpense, dan (e) Nanonets	71
Gambar 3.3 Contoh gambar struk (f) Roboflow dan (g) UniqueData	72
Gambar 3.4 Contoh gambar struk (h) SROIE-v2, (i) Primary, dan (j) Threads	72
Gambar 3.5 Flowchart alur sistem utama Klaudia	81
Gambar 3.6 Use case diagram sistem Klaudia	83
Gambar 3.7 Activity diagram proses validasi masukan dan guardrails	84
Gambar 3.8 Activity diagram proses routing, ekstraksi, dan orkestrasi data entry	85
Gambar 3.9 Class diagram model data pengguna dan dokumen	86
Gambar 3.10 Class diagram komponen guardrails	87
Gambar 3.11 Class diagram hierarki agent dan MCP server	88
<page_number>viii</page_number>

Page 9
Gambar 3.12 Sequence diagram proses upload struk hingga data entry ke Google Sheets ................................................................................................................ 89 Gambar 3.13 Sequence diagram fase permintaan data entry dan HITL................................................ 90 Gambar 3.14 Sequence diagram fase konfirmasi dan penulisan ke Google Sheets ................................................ 91 Gambar 3.15 End-to-end LLMOps pipeline sistem Klaudia ................................................................................ 92 Gambar 3.16 Rancangan antarmuka pengguna sistem Klaudia ............................................................................ 93 Gambar 3.17 Contoh gambar struk pembelian, skema ekstrasi ............................................................................ 94 Gambar 3. 18 Contoh hasil ekstrasi ................................................................................................................ 94 Gambar 3.19 Contoh ilustrasi ground-truth dan hasil prediksi GLM-OCR ............................................................ 96 Gambar 3.20 Struktur pohon hierarki dari contoh ilustrasi Gambar 3.17.............................................................. 100 Gambar 3.21 Perbandingan ground truth dan prediksi model ........................................................................... 105

<page_number>ix</page_number>

Page 10
DAFTAR TABEL
Tabel 1. 1 Tinjauan penelitian terdahulu	11
Tabel 2.1 Perbandingan model dalam parsing dokumen & ekstraksi	34
Tabel 2.2 Perbandingan model dalam skenario dunia nyata	35
Tabel 2.3 Perbandingan model dalam kecepatan inferensi	35
Tabel 2.4 Komparasi performa model frontier pada benchmark Agentic AI	49
Tabel 2.5 Simbol - simbol flowchart diagram	68
Tabel 2.6 Simbol-simbol activity diagram	71
Tabel 2.7 Simbol – simbol class diagram	72
Tabel 2.8 Simbol – simbol sequence diagram	74
Tabel 3.1 Waktu penelitian	74
Tabel 3.2 Spesifikasi perangkat keras	77
Tabel 3.3 Spesifikasi perangkat lunak	78
Tabel 3.4 Struktur grup ground-truth dan prediksi	97
Tabel 3.5 Matriks Skor Pencocokan Sn, m untuk Grup Items	98
Tabel 3.6 Hasil pasangan grup setelah Hungarian Matching	98
Tabel 3.7 Perhitungan TP, FP, FN per setiap pasangan grup	98
Tabel 3.8 Pemetaan tipe data ANLS* pada struktur evaluasi	101
Tabel 3.9 Matriks skor ANLS* pairwise antar item	101
Tabel 3.10 Perhitungan NLS per field pada setiap pasangan yang dicocokkan	102
Tabel 3.11 Rekapitulasi kontribusi setiap komponen terhadap ANLS*	104
Tabel 3.12 Field harga evaluasi digit accuracy	104
Tabel 3.13 Perbandingan hasil normalisasi	105
Tabel 3.14 Kasus 1 AST akurasi	107
Tabel 3. 15 Kasus 2 AST akurasi	108
Tabel 3.16 Kasus 1 Pass@1	109
Tabel 3.17 Kasus 2 Pass@1	110
Tabel 3.18 Skenario pengujian black box	111
<page_number>X</page_number>

Page 11
BAB I PENDAHULUAN

1.1 Latar Belakang Proses data entry secara manual merupakan salah satu aktivitas operasional yang paling rentan terhadap kesalahan dalam dunia bisnis. Tingkat kesalahan pada entri data manual secara konsisten berkisar antara 0.55% hingga 3.6% per field, dan dapat mencapai 26,9% pada kondisi tertentu akibat faktor kelelahan serta distraksi operator manusia (Mays dan Mathias, 2019; Barchard dkk., 2020). Penelitian empiris menunjukkan bahwa metode verifikasi visual (visual checking) menghasilkan risiko kesalahan yang jauh lebih tinggi dibandingkan pendekatan otomatis. Kesalahan tersebut, meskipun tampak kecil pada skala individual, dapat mengakibatkan ketidakakuratan yang signifikan dalam laporan keuangan apabila tidak terdeteksi dan terkoreksi lebih awal. Dalam konteks pencatatan transaksi berbasis struk pembelian, permasalahan ini diperburuk oleh variasi format struk yang sangat beragam antar merchant, tipografi yang tidak konsisten, serta kualitas cetakan yang sering kali kurang optimal. Kondisi ini menjadikan entri data dari struk pembelian sebagai salah satu kasus data entry yang paling menantang untuk diotomatisasi secara akurat.

Permasalahan entri data manual memiliki relevansi yang tinggi dalam konteks Indonesia, baik pada tingkat individu maupun organisasi. Dalam pengelolaan keuangan pribadi, banyak masyarakat masih mengandalkan pencatatan pengeluaran secara tradisional, seperti menyimpan dan mencatat struk belanja pada kertas, buku catatan, atau dompet secara tidak terstruktur. Praktik ini sering kali tidak dilakukan secara rutin karena keterbatasan waktu, aktivitas yang padat, serta rendahnya kebiasaan pencatatan keuangan, sehingga detail transaksi mudah terlupakan atau tidak tercatat secara lengkap (Shaharudin dkk., 2025). Kondisi serupa juga terjadi pada sektor Usaha Mikro, Kecil, dan Menengah (UMKM), di mana sebagian pelaku usaha masih mencatat transaksi pembelian maupun pengeluaran usaha secara manual pada buku kas sederhana. Metode ini tidak hanya memerlukan waktu lebih lama, tetapi juga meningkatkan risiko kesalahan

<page_number>1</page_number>

Page 12
<page_number>2</page_number>

pencatatan, salah perhitungan, serta kehilangan bukti transaksi seperti struk atau nota pembelian (Perdanawati, 2025; Ulfha dkk., 2025). Selain itu, dalam lingkungan perusahaan, struk pembelian sering kali menjadi dokumen penting dalam proses klaim reimbursement karyawan. Proses yang masih bergantung pada pengumpulan bukti fisik dan entri data manual berpotensi menimbulkan berbagai kendala, seperti kehilangan dokumen, kesalahan input nominal atau tanggal, serta keterlambatan verifikasi oleh bagian keuangan (Fernanda dan Sawitri, 2025; Pakpahan dkk., 2025). Berbagai kondisi tersebut menunjukkan bahwa pencatatan transaksi berbasis struk pembelian masih menghadapi tantangan signifikan dalam hal efisiensi, akurasi, dan konsistensi pencatatan data, sehingga memerlukan solusi otomatisasi yang mampu mendukung transformasi pencatatan keuangan menuju sistem yang lebih digital dan terintegrasi.

Pendekatan otomatisasi tradisional menggunakan Optical Character Recognition (OCR) telah lama diterapkan untuk mengekstrak teks dari dokumen, namun memiliki keterbatasan yang signifikan. Dalam penelitian yang dilakukan oleh Indrakusuma dkk, (2021), menunjukkan bahwa sistem OCR berbasis Tesseract yang dikombinasikan dengan Support Vector Machine memerlukan waktu pemrosesan rata-rata 8,89 detik per dokumen dan pada setiap proses pemindaian masih menghasilkan sekitar 1–2 kesalahan pembacaan maupun klasifikasi. Pendekatan serupa yang mengandalkan Tesseract dan Regular Expressions masih bergantung pada aturan tetap (rule-based parsing) untuk mengekstrak informasi dari struk. Ketergantungan pada pola yang telah ditentukan membuat metode ini kurang adaptif terhadap variasi format struk serta rentan menghasilkan ekstraksi yang tidak akurat ketika kualitas gambar buruk atau struktur struk berbeda dari pola yang telah didefinisikan (Setiawan dkk., 2025). Implementasi OCR berbasis Convolutional Neural Network (CNN) untuk ekstraksi teks gambar menghasilkan F1-score 49,18% pada deteksi dan Correctly Recognized Word 55,80% pada pengenalan (Wijaya dan Lubis, 2022). Demikian pula, OCR CNN untuk data e-KTP mencapai error rate 5% dalam 30 detik, namun membutuhkan koreksi manual pada field yang terpotong akibat kualitas citra yang bervariasi (Sugiarta, Andini dan Hidayatullah, 2021). Keterbatasan mendasar OCR tradisional terletak pada

Page 13
<page_number>3</page_number>

ketidakmampuannya memahami struktur semantik dokumen, OCR hanya menghasilkan teks mentah tanpa informasi tentang makna atau hubungan semantik antar elemen teks.

Bidang pemahaman dokumen telah mengalami pergeseran paradigma dari OCR tradisional menuju Vision Language Model (VLM) yang mampu memproses dokumen secara end-to-end. Kim dkk., 2022 memperkenalkan Donut, sebuah OCR-free Document Understanding Transformer yang memetakan citra dokumen langsung ke token JSON terstruktur tanpa memerlukan tahapan OCR terpisah, dan mencapai hasil state-of-the-art pada benchmark CORD dan DocVQA. Perkembangan selanjutnya menghasilkan VLM skala kecil seperti GLM-OCR dengan hanya 0,9 miliar parameter, yang mencapai skor 94,62 pada OmniDocBench V1.5 serta 94,5% pada skenario Receipt Key Information Extraction (KIE) dunia nyata (Duan, S. dkk., 2026). Tinjauan sistematis oleh Rombach & Fettke, 2026 terhadap 130 pendekatan KIE berbasis deep learning pada dokumen bisnis menunjukkan bahwa metode berbasis LLM pertama kali muncul dalam penelitian KIE pada tahun 2023 dan menjadi kategori kedua terbanyak pada tahun 2024, mengonfirmasi transisi cepat dari pendekatan konvensional ke pendekatan berbasis model bahasa. Kemampuan VLM dalam memahami konteks visual dokumen secara holistik, termasuk hubungan spasial dan semantik antar elemen, menjadikannya solusi yang lebih tepat untuk tugas KIE dari dokumen semi-structured seperti struk pembelian dibandingkan dengan pendekatan berbasis aturan atau OCR tradisional.

Meskipun VLM telah menunjukkan kemampuan ekstraksi informasi yang tinggi, proses otomatisasi data entry tidak berhenti pada tahap ekstraksi. Data yang telah diekstrak perlu diteruskan ke database, spreadsheet, atau sistem pencatatan lainnya secara aman dan tervalidasi. Kebutuhan ini memerlukan sistem orkestrasi yang mampu mengoordinasikan berbagai komponen secara otonom. Paradigma Agentic AI, mengacu pada sistem kecerdasan buatan otonom dengan kemampuan adaptasi, pengambilan keputusan tingkat lanjut, dan kemandirian operasional (Abou Ali, 2025). Pengembangan sistem agentic selanjutnya didukung oleh inovasi arsitektur seperti Model Context Protocol (MCP) yang diperkenalkan oleh

Page 14
<page_number>4</page_number>

Anthropic pada November 2024 sebagai standar terbuka untuk integrasi agent-tool (Hou dkk., 2025). MCP menggunakan arsitektur client-server berbasis JSON-RPC 2.0, dan pada Desember 2025 telah didonasikan kepada Agentic AI Foundation di bawah Linux Foundation dengan dukungan dari OpenAI, Google, dan Microsoft.

Berdasarkan tinjauan terhadap literatur yang ada, ditemukan bahwa penelitian-penelitian sebelumnya dalam domain KIE struk pembelian hanya berfokus pada tahap ekstraksi informasi tanpa menangani alur hilir berupa entri data otomatis ke sistem pencatatan. Framework multi-agent seperti MetaGPT (Hong dkk., 2024) dan AutoGen (Wu dkk., 2023) mendemonstrasikan pola kolaborasi yang kuat namun menggunakan integrasi tool secara ad-hoc. Belum terdapat penelitian akademis yang menggabungkan VLM ter-fine-tune berskala kecil untuk KIE struk pembelian dengan orkestrasi hierarchical multi-agent berbasis MCP dalam satu pipeline end-to-end. Selain itu, evaluasi pada penelitian sebelumnya umumnya mengukur kualitas ekstraksi atau kinerja agent secara terpisah, bukan keduanya dalam satu sistem terintegrasi.

Berdasarkan latar belakang serta kesenjangan penelitian yang telah diuraikan, diusulkan penelitian dengan judul "Otomatisasi Entri Data Struk Pembelian Menggunakan Vision-Language Model (VLM) dengan Fine-Tuning LoRA serta Orkestrasi Multi-Agent Hierarkis Berbasis Model Context Protocol (MCP)". Penelitian ini mengembangkan sistem bernama Klaudia yang menggunakan GLM-OCR 0,9B yang di-fine-tune dengan Low-Rank Adaptation (LoRA) melalui LLAMA Factory untuk ekstraksi informasi kunci dari struk pembelian, diorkestrasi melalui arsitektur Hierarchical Agent Teams menggunakan LangGraph dengan MCP-SQLite dan MCP-GSheets sebagai batas eksekusi tool, dilindungi oleh guardrails ganda (Llama Prompt Guard 2 dan LLM-as-Judge), serta dilengkapi mekanisme Human-in-the-Loop (HITL) sebelum operasi penulisan data. Kinerja sistem dievaluasi secara komprehensif menggunakan metrik ekstraksi (KIEval dan ANLS*) serta metrik agentic (AST accuracy dan Pass@K).

Page 15
<page_number>5</page_number>

1.2 Rumusan Masalah
Berdasarkan latar belakang yang telah diuraikan sebelumnya, rumusan masalah dalam penelitian ini adalah sebagai berikut:

Bagaimana merancang model yang mampu mengekstrak informasi kunci dari foto struk pembelian berbasis semantik dengan GLM-OCR 0.9B?
Bagaimana membangun sistem yang mampu secara otomatis melakukan entri data ke dalam sistem pencacatan digital berupa spreadsheet tanpa memerlukan pengetikan ulang secara manual dengan arsitektur Hierarchical Multi-Agent berbasis MCP?
1.3 Batasan Masalah
Adapun batasan masalah yang ditetapkan peneliti agar pembahasan dari penulisan ini tidak melenceng jauh dari topik utama yaitu sebagai berikut:

Dokumen yang diproses terbatas hanya pada hasil cetakan struk pembelian dalam format foto (JPG, PNG) dan PDF.
Sistem hanya melakukan pengenalan dan pencatatan data dari hasil ekstrasi ke dalam Google Sheets sebagai media spreadsheet tujuan, tidak mencakup integrasi dengan aplikasi akuntansi atau sistem pencatatan keuangan lainnya.
Antarmuka sistem diimplementasikan pada platform mobile iOS dan tidak mencakup pengembangan versi Android atau web secara penuh pada tahap penelitian ini.
1.4 Tujuan Penelitian
Adapun tujuan dari penelitian ini adalah sebagai berikut:

Merancang model berbasis kecerdasan buatan yang mampu mengekstrak informasi kunci (key information extraction) dari foto struk pembelian berbasis semantik dengan GLM-OCR 0.9B.
Membangun sistem berbasis kecerdasan buatan yang mampu secara otomatis memasukkan data hasil pengenalan ke dalam Google Sheets tanpa
Page 16
<page_number>6</page_number>

memerlukan pengetikan ulang secara manual oleh pengguna dengan arsitektur Hierarchical Multi-Agent berbasis MCP.

1.5 Manfaat Penelitian Adapun manfaat dari penelitian ini adalah sebagai berikut:

Memberikan solusi otomatisasi pencatatan transaksi dari struk pembelian yang dapat mengurangi kesalahan entri data manual dan mempercepat proses pencatatan keuangan.
Memberikan kontribusi ilmiah berupa arsitektur sistem yang mengintegrasikan pengenalan dokumen berbasis kecerdasan buatan dengan pencatatan data otomatis, yang dapat menjadi referensi bagi penelitian selanjutnya di bidang otomatisasi pemrosesan dokumen keuangan.
1.6 Sistematika Penulisan Laporan Adapun sistematika penulisan yang digunakan dalam penyusunan penelitian ini adalah sebagai berikut: BAB I PENDAHULUAN Bab ini memuat latar belakang permasalahan entri data manual dan kebutuhan otomatisasi berbasis Agentic AI, rumusan masalah, batasan masalah, tujuan penelitian, manfaat penelitian, sistematika penulisan, serta tinjauan pustaka yang mengkaji penelitian terdahulu terkait ekstraksi informasi dokumen dan sistem multi-agent. BAB II LANDASAN TEORI Bab ini menguraikan landasan teoretis yang mendukung penelitian, dimulai dari konsep semi-structured data dan data entry. Pembahasan mendalam dilakukan pada teknologi Large Language Model (LLM) yang mencakup arsitektur Transformer, metode fine-tuning (instruction dan LORA), hingga Vision Language Model (VLM). Selanjutnya, dijelaskan pula konsep Agentic AI dan Multi-Agent System (MAS) dengan pendekatan hierarchical agent teams, Human-in-the-Loop (HITL), serta Model Context Protocol (MCP). Bagian akhir bab ini memaparkan perangkat pengembangan seperti SQLite, React Native, dan Expo, serta metodologi Agile Scrum dan blackbox sebagai teknik pengujian sistem

Page 17
<page_number>7</page_number>

BAB III METODOLOGI PENELITIAN

Bab ini menjelaskan secara rinci langkah-langkah kerja yang dilakukan dalam penelitian. Cakupannya meliputi metode pengumpulan data, metode pengembangan sistem menggunakan Agile Scrum, waktu dan tempat penelitian, analisis kebutuhan sistem secara fungsional dan nonfungsional, serta rancangan sistem yang mencakup rancangan arsitektur sistem, rancangan proses, rancangan data, dan rancangan antarmuka pengguna.

BAB IV HASIL IMPLEMENTASI DAN PENGUJIAN SISTEM

Bab ini menyajikan implementasi sistem secara detail, analisis hasil fine-tuning GLM-OCR, evaluasi kinerja ekstraksi menggunakan KIEval dan ANLS*, evaluasi kinerja agent menggunakan AST accuracy dan Pass@K, serta pembahasan hasil pengujian blackbox.

BAB IV PENUTUP

Bab ini memuat kesimpulan dari penelitian yang telah dilakukan serta saran untuk pengembangan sistem selanjutnya.

1.7 Tinjauan Pustaka

Berikut rangkuman penelitian terdahulu yang berkaitan dengan otomatisasi data entry struk pembelian, teknologi Optical Character Recognition (OCR), ekstraksi informasi dokumen, serta penerapan Agentic AI dan arsitektur multi-agent yang menjadi rujukan dalam penyusunan penelitiawn ini.

Penelitian pertama dilakukan oleh Setiawan dkk., (2025) dengan judul "Ekstraksi Informasi Struk Belanja Melalui Pemanfaatan Tesseract dan Regular Expressions". Penelitian tersebut membangun sistem ekstraksi struk belanja untuk membantu proses pencatatan keuangan dengan menerapkan model YOLO untuk mendeteksi area struk, Tesseract untuk mengekstrak teks dari gambar, dan Regular Expressions untuk mengolah data menjadi terstruktur berupa nama produk, kuantitas, harga satuan, total harga, dan diskon. Hasil pengujian beta menggunakan User Acceptance Testing terhadap 37 responden menunjukkan rata-rata nilai 4,47 dari skala 5, namun sistem ini masih bergantung pada aturan parsing yang telah ditetapkan (rule-based) yang kurang adaptif terhadap variasi format struk yang

Page 18
<page_number>8</page_number>

berbeda, serta hasil ekstraksi Tesseract menjadi kurang akurat pada kondisi struk yang terlipat, buram, atau mengandung banyak noise, dan keluaran sistem hanya berhenti pada tampilan data terstruktur tanpa kemampuan untuk secara otomatis memasukkan data ke dalam sistem pencatatan seperti spreadsheet atau database.

Penelitian kedua dilakukan oleh Yan dkk., (2025) dan dipublikasikan pada tahun 2024 di jurnal Information Processing & Management (Elsevier) dengan judul "DocExtractNet: A Novel Framework for Enhanced Information Extraction from Business Documents". Penelitian tersebut mengembangkan framework berbasis LayoutLMv3 dengan tiga modul tambahan, yaitu ImageEnhance untuk pengenalan citra berkualitas rendah, PrecisionHints untuk melengkapi pasangan kunci-nilai yang hilang, dan CrossModalFusion untuk menggabungkan fitur citra dan teks. Hasil evaluasi menunjukkan bahwa DocExtractNet mencapai F1 sebesar 97,07% pada Finance-Receipts, 91,80% pada FUNSD, dan 97,38% pada CORD. Penelitian ini merepresentasikan kemajuan terkini dalam KIE multimodal berbasis Transformer yang memerlukan tahapan OCR terpisah dan tidak menangani alur hilir berupa entri data otomatis.

Penelitian ketiga dipublikasikan pada tahun 2025 di jurnal Scientific Reports (Nature) dengan judul "LLM-TKIE: Large Language Model Driven Transferable Key Information Extraction Mechanism for Nonstandardized Tables". Metode yang digunakan meliputi pipeline deteksi teks dan pengenalan teks, diikuti oleh penalaran semantik berbasis LLM dengan few-shot learning tanpa fine-tuning. Hasil yang diperoleh menunjukkan F1 sebesar 80,9% dan TED-accuracy 88,85% pada dataset CORD, serta F1 sebesar 83,9% pada SROIE tanpa proses fine-tuning. Pendekatan ini mengungguli model multimodal state-of-the-art sebesar 5–8% pada data domain yang belum diberi label, namun tidak menggunakan VLM end-to-end dan tidak menangani proses entri data hilir (Hu dkk., 2025).

Penelitian keempat dilakukan pada tahun 2024 dan dipublikasikan di arXiv dengan judul "STNet: See then Tell: Enhancing Key Information Extraction with Vision Grounding". Model yang diusulkan bersifat OCR-free dan menggunakan token khusus untuk vision grounding serta physical decoder yang terspesialisasi. GPT-4 dimanfaatkan untuk konstruksi dataset pelatihan. Hasil evaluasi

Page 19
<page_number>9</page_number>

menunjukkan pencapaian state-of-the-art pada benchmark CORD, SROIE, dan DocVQA. Penelitian ini merepresentasikan batas kemampuan terkini dalam KIE tanpa OCR, namun tidak mencakup integrasi dengan sistem agent untuk otomatisasi data entry (S. Liu dkk., 2025).

Penelitian kelima dilakukan oleh Kim dkk., (2022) dan dipresentasikan di ECCV 2022 dengan judul "OCR-free Document Understanding Transformer (Donut)". Model yang diusulkan merupakan Transformer encoder-decoder yang memetakan citra dokumen langsung ke token JSON terstruktur tanpa memerlukan OCR, dan di-pre-train menggunakan generator data sintetis SynthDoG. Donut mencapai hasil state-of-the-art pada CORD document parsing, klasifikasi RVL-CDIP, dan DocVQA, serta mengungguli metode berbasis OCR dalam hal kecepatan dan akurasi. Penelitian ini merupakan karya seminal dalam pendekatan OCR-free yang menjadi fondasi bagi pengembangan VLM untuk pemahaman dokumen.

Penelitian keenam dilakukan oleh Zheng dkk., 2024 dan dipublikasikan di ACL 2024 System Demonstrations dengan judul "LlamaFactory: Unified Efficient Fine-Tuning of 100+ Language Models". LLaMA Factory merupakan framework terpadu yang mengintegrasikan berbagai teknik adaptasi model termasuk LoRA, QLoRA, GaLore, BAdam, dan freeze-tuning untuk lebih dari 100 LLM dan VLM. Framework ini juga menyediakan antarmuka web LlamaBoard serta mendukung pelatihan SFT, RLHF, DPO, dan ORPO. Hasil evaluasi menunjukkan bahwa LoRA dan QLoRA mencapai performa terbaik dibandingkan full fine-tuning pada sebagian besar kasus. Penelitian ini menjadi fondasi teknis bagi proses fine-tuning GLM-OCR dalam penelitian yang diusulkan.

Penelitian ketujuh dilakukan oleh Hong dkk., (2024) dan dipresentasikan sebagai Oral paper (1,2% teratas) di ICLR 2024 dengan judul "MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework". MetaGPT mengkodekan Standardized Operating Procedures (SOP) ke dalam urutan prompt untuk kolaborasi multi-agent, dengan pembagian peran spesialis dalam paradigma lini perakitan. Hasil evaluasi menunjukkan pencapaian state-of-the-art pada HumanEval dan MBPP dengan peningkatan absolut 5,4% pada MBPP melalui umpan balik eksekutif, serta pengurangan cascading hallucinations melalui

Page 20
<page_number>10</page_number>

keluaran antara yang terstruktur. Penelitian ini menjadi acuan utama untuk pola arsitektur hierarchical multi-agent yang diadaptasi dalam penelitian ini dengan konteks pemrosesan dokumen dan penggunaan MCP sebagai batas tool.

Penelitian kedelapan dilakukan oleh Wu dkk., (2023) dari Microsoft Research dan Penn State pada tahun 2023, dipublikasikan di COLM 2024 dengan judul "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation". AutoGen menggunakan konsep conversable agents yang mendukung LLM, masukan manusia, dan tool dalam pola percakapan yang dapat dikonfigurasi, serta menyediakan dukungan Human-in-the-Loop secara native. Sistem ini telah didemonstrasikan pada berbagai domain termasuk matematika, coding, tanya-jawab, dan pengambilan keputusan, serta menempati peringkat pertama pada benchmark GAIA. Penelitian ini menjadi referensi penting untuk integrasi HITL dalam sistem multi-agent, yang dalam penelitian ini diimplementasikan menggunakan mekanisme interrupt pada LangGraph.

Penelitian kesembilan dilakukan oleh Patil dkk., (2025) dari UC Berkeley dan dipublikasikan di ICML 2025 dengan judul "The Berkeley Function Calling Leaderboard (BFCL): From Tool Use to Agentic Evaluation of Large Language Models". BFCL merupakan benchmark untuk mengevaluasi kemampuan function-calling LLM menggunakan Abstract Syntax Tree (AST). Evaluasi AST menangkap kebenaran fungsi yang dipanggil, nama parameter, dan tipe parameter tanpa memerlukan eksekusi. Benchmark ini mencakup lebih dari 2.200 kasus uji lintas Python, Java, JavaScript, dan SQL. Hasil evaluasi menunjukkan bahwa model terbaik unggul pada panggilan single-turn namun masih menghadapi tantangan pada penalaran multi-step. Metrik AST accuracy dari penelitian ini diadopsi sebagai salah satu metrik evaluasi kinerja agent dalam penelitian yang diusulkan.

Penelitian kesepuluh dilakukan oleh Khang dkk., (2025) dari Upstage AI dan dipublikasikan di ICDAR 2026 dengan judul "KIEval: Evaluation Metric for Document Key Information Extraction". KIEval merupakan metrik berorientasi aplikasi yang mengevaluasi kualitas ekstraksi pada tingkat entitas dan tingkat grup secara bersamaan, menggunakan algoritma Hungarian matching antara grup

Page 21
<page_number>11</page_number>

prediksi dan ground truth. Hasil evaluasi menunjukkan bahwa metrik Entity F1 konvensional memberikan skor 1,0 bahkan ketika pengelompokan salah, namun KIEval mampu memberikan penalti terhadap ketidaksesuaian struktural secara tepat. Metrik ini sangat relevan untuk evaluasi ekstraksi struk pembelian karena hubungan antara nama item, kuantitas, dan harga harus dipertahankan secara struktural.

Penelitian kesebelas dilakukan oleh Peer dkk., (2025) dari DeepOpinion pada tahun 2025 dan dipublikasikan di arXiv dengan judul "ANLS - A Universal Document Processing Metric for Generative Large Language Models". ANLS* memperluas metrik ANLS klasik untuk menangani struktur keluaran yang kompleks dengan memetakan prediksi dan ground truth ke dalam struktur pohon (tree). Metrik ini mendukung perbandingan string, tuple, list, dan dictionary dengan penalti terhadap halusinasi. Hasil evaluasi dilakukan menggunakan GPT-4, Claude-3, dan Gemini pada tujuh dataset dokumen termasuk SROIE dan VRDU. Kemampuan ANLS* dalam menangani keluaran JSON bersarang menjadikannya sangat relevan untuk mengevaluasi skema ekstraksi struk pembelian yang memiliki struktur hierarkis seperti info, items, dan payment.

Rangkuman dari beberapa penelitian terdahulu yang telah dijelaskan sebelumnya dapat dilihat pada Tabel 1.1 berikut.

Tabel 1. 1 Tinjauan penelitian terdahulu

No.	Judul	Metode	Hasil
1.	Ekstraksi Informasi Struk Belanja Melalui Pemanfaatan Tesseract dan Regular Expressions	YOLO untuk deteksi area struk, Tesseract OCR untuk ekstraksi teks, dan Regular Expressions untuk parsing data terstruktur	Pengujian hanya pada deteksi *layout* struk dengan F1 *score* 0.88, tanpa melakukan evaluasi pada hasil proses ekstrasi berbasis *regex*
Page 22
<page_number>12</page_number>

Tabel 1. 1 Tinjauan penelitian terdahulu (Lanjutan)

No.	Judul	Metode	Hasil
2.	DocExtractNet: A Novel Framework for Enhanced Information Extraction from Business Documents	LayoutLMv3 dengan modul Image Enhance, Precision Hints, dan Cross Modal Fusion	F1 score 97,07% pada Finance-Receipts, 91,80% pada FUNSD, 97,38% pada CORD
3.	LLM-TKIE: Large Language Model Driven Transferable Key Information Extraction	Pipeline deteksi teks + pengenalan teks, diikuti penalaran LLM dengan few-shot learning	F1 80,9% pada CORD; F1 83,9% pada SROIE tanpa fine-tuning
4.	STNet: See then Tell: Enhancing KIE with Vision Grounding	Model OCR-free dengan token vision grounding dan physical decoder	State-of-the-art pada CORD, SROIE, dan DocVQA. Memberikan grounding visual bersamaan dengan output teks.
5.	Donut: OCR-free Document Understanding Transformer	Transformer encoder-decoder yang memetakan citra dokumen langsung ke token JSON	State-of-the-art pada CORD document parsing, klasifikasi RVL-CDIP, dan DocVQA. Lebih cepat dan akurat dibandingkan pipeline berbasis OCR.
Page 23
<page_number>13</page_number>

Tabel 1. 1 Tinjauan penelitian terdahulu (Lanjutan)

No.	Judul	Metode	Hasil
6.	LlamaFactory: Unified Efficient Fine-Tuning of 100+ Language Models	Framework terpadu dengan LoRA, QLoRA, GaLore, BAdam untuk 100+ LLM/VLM	LoRA dan QLoRA mencapai performa terbaik vs. full fine-tuning
7.	MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework	Standardized Operating Procedures (SOP) dalam prompt multi-agent hierarkis	State-of-the-art pada HumanEval dan MBPP; peningkatan 5,4% pada MBPP
8.	AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation	Conversable agents dengan HITL native dan pola percakapan yang dapat dikonfigurasi	Peringkat #1 pada benchmark GAIA
9.	BFCL: From Tool Use to Agentic Evaluation of LLMs	Evaluasi function-calling menggunakan perbandingan Abstract Syntax Tree (AST)	2.200+ kasus uji; AST accuracy berkorelasi dengan executable accuracy
10.	KIEval: Evaluation Metric for Document Key Information Extraction	Metrik evaluasi entity-level dan group-level dengan Hungarian matching	Mendeteksi kesalahan struktural yang tidak tertangkap oleh Entity F1 konvensional
11.	ANLS*: A Universal Document Processing Metric for Generative LLMs	Perbandingan struktur pohon untuk string, tuple, list, dan dictionary	Evaluasi pada 7 dataset dengan GPT-4, Claude-3, dan Gemini
Page 24
<page_number>14</page_number>

Berdasarkan tinjauan pustaka yang telah dikaji, penelitian-penelitian sebelumnya dalam domain pemrosesan struk pembelian memiliki beberapa keterbatasan fungsional yang belum terselesaikan. Dari sisi pengenalan dokumen, penelitian di Indonesia masih mengandalkan OCR konvensional berbasis Tesseract yang dikombinasikan dengan aturan parsing manual menggunakan Regular Expressions, di mana pendekatan ini tidak mampu memahami makna dan hubungan antar informasi pada struk secara kontekstual dan hanya mencocokkan pola teks yang telah ditentukan sebelumnya. Dari sisi dataset, benchmark yang umum digunakan seperti SROIE hanya berisi struk hasil pemindaian (scan) dengan kualitas seragam yang tidak merepresentasikan kondisi nyata saat pengguna memfoto struk menggunakan kamera ponsel dengan variasi sudut pengambilan, pencahayaan, dan jarak yang beragam. Dataset CORD, meskipun berasal dari Indonesia, hanya berfokus pada struk restoran dengan informasi yang telah disederhanakan pada bagian item dan pembayaran, tanpa menampilkan elemen visual lainnya seperti informasi toko, kontak, nomor pajak, dan promosi yang pada kenyataannya hadir pada struk dan dapat mempersulit proses pengenalan. Dari sisi fungsionalitas, seluruh penelitian yang dikaji hanya berhenti pada tahap OCR dan pengenalan informasi dari struk tanpa menyediakan kemampuan untuk secara otomatis memasukkan data hasil pengenalan ke dalam sistem pencatatan seperti spreadsheet atau database, yang berarti pengguna masih harus menyalin data secara manual setelah proses pengenalan selesai. Oleh karena itu, diusulkan penelitian dengan judul "Otomatisasi Entri Data Struk Pembelian Menggunakan Vision-Language Model (VLM) dengan Fine-Tuning LoRA serta Orkestrasi Multi-Agent Hierarkis Berbasis Model Context Protocol (MCP)" yang tidak hanya mengenali informasi dari foto struk secara akurat menggunakan model kecerdasan buatan yang telah dilatih khusus untuk berbagai jenis format struk pembelian, tetapi juga secara otomatis memasukkan data tersebut ke dalam Google Sheets melalui sistem agent cerdas yang terkoordinasi, dilengkapi mekanisme konfirmasi oleh pengguna sebelum data disimpan untuk menjamin kebenaran pencatatan.

Page 25
BAB II LANDASAN TEORI

2.1 Struk Pembelian

Struk pembelian atau nota belanja merupakan dokumen bukti transaksi keuangan yang dihasilkan dari aktivitas pembelian dan memuat informasi terstruktur mengenai detail transaksi. Secara teknis, struk berfungsi sebagai sumber data primer yang merekam atribut penting seperti nama entitas pedagang (merchant), deskripsi produk, kuantitas, harga satuan, nilai total belanja, metode pembayaran, hingga tanggal dan waktu transaksi. Dalam konteks document understanding, struk pembelian termasuk dalam kategori visually-rich document yang mengandung banyak nilai numerik dan memerlukan kemampuan discrete reasoning untuk menjawab pertanyaan terkait harga, kuantitas, dan total pembayaran (Begaev dan Orlov, 2023). Miliaran struk dicetak setiap tahun secara global untuk keperluan pencatatan pengeluaran, pengelolaan keuangan, dan pelaporan akuntansi, baik pada tingkat individu maupun organisasi (Rexhepi dkk., 2025).

Meskipun memiliki elemen informasi yang serupa secara semantik antar dokumen, struk pembelian menyajikan tantangan ekstraksi yang kompleks akibat karakteristik fisiknya yang khas. Variasi tata letak (layout) yang sangat dinamis antar sistem kasir, kualitas cetakan yang rentan pudar (faded), keberadaan derau (noise) pada citra hasil foto, serta perbedaan format representasi untuk entitas yang secara semantik identik, seperti tanggal, nama produk yang disingkat, dan format harga, menjadikan proses ekstraksi informasi dari struk tidak dapat diselesaikan dengan pencocokan pola statis semata. Kondisi ini mendorong kebutuhan akan pendekatan berbasis deep learning yang mampu memetakan citra struk secara langsung menjadi structured key-value fields yang akurat, tanpa bergantung pada aturan ekstraksi yang telah ditentukan sebelumnya untuk setiap format struk.

<page_number>15</page_number>

Page 26
<page_number>16</page_number>

2.2 Semi-Structured Data
Semi-structured data merupakan kategori data yang tidak mengikuti skema relasional yang kaku seperti tabel database, namun memiliki struktur parsial berupa tag, hierarki, atau penanda yang membedakannya dari data tidak terstruktur sepenuhnya (Li, Jiang dan Song, 2023). Berbeda dengan structured data di mana setiap field telah terdefinisi secara eksplisit dan konsisten, semi-structured data memiliki variasi dalam tata letak, urutan kemunculan field, dan kelengkapan informasinya antar dokumen.

Struk pembelian merupakan salah satu contoh semi-structured data yang paling umum ditemui dalam lingkup bisnis ritel. Setiap struk mengandung elemen informasi yang serupa secara semantik, seperti nama toko, tanggal transaksi, daftar item, dan total pembayaran, namun format visualnya sangat bervariasi antar merchant (Ylisiurunen, 2022). Variasi ini mencakup perbedaan tipografi, layout kolom, penempatan logo, penggunaan singkatan nama produk, serta representasi harga dan tanggal yang beragam bergantung pada sistem kasir yang digunakan oleh masing-masing merchant.

Tantangan utama dalam pemrosesan semi-structured data pada dokumen bisnis adalah ketidakkonsistenan representasi untuk entitas yang secara semantik identik. Tanggal yang sama dapat direpresentasikan sebagai "01/01/2025", "1 Januari 2025", atau "2025-01-01". Nama produk dapat disingkat atau dieja lengkap. Kondisi ini menjadikan pemrosesan struk pembelian sebagai permasalahan Key Information Extraction (KIE) yang membutuhkan pemahaman kontekstual, bukan sekadar pencocokan pola berbasis aturan statis (Abdalla dkk., 2025).

Karakteristik visually-rich document pada struk pembelian menambahkan dimensi kompleksitas tersendiri. Posisi spasial elemen teks dalam ruang dua dimensi membawa makna semantik yang tidak kalah penting dari konten teksnya. Informasi header toko di bagian atas, daftar item di tengah, dan ringkasan pembayaran di bawah membentuk struktur visual yang konsisten secara semantik meskipun variatif secara visual antar dokumen (Kasem, M. S. dkk, 2026).

Page 27
<page_number>17</page_number>

2.3 Data Entry
Data entry didefinisikan sebagai serangkaian proses terstruktur yang bertujuan untuk memastikan data yang diterima, dimasukkan, diproses, dan dikelola dalam suatu sistem bersifat akurat, lengkap, konsisten, reliabel, dan layak untuk dianalisis secara statistik. Tidak hanya terbatas pada aktivitas memasukkan data ke dalam sistem, data entry mencakup tahapan yang lebih luas seperti penerimaan dan pelacakan data, proses input, validasi, pembersihan data, pengendalian perubahan, hingga rekonsiliasi dan transfer data ke basis data akhir (Society for Clinical Data Management, 2023).

Kualitas hasil data entry dapat diukur melalui enam dimensi utama, yaitu akurasi, kelengkapan, konsistensi, ketepatan waktu, validitas, dan keunikan data (Syed dkk., 2023). Proses manual yang dilakukan oleh operator manusia rentan terhadap penurunan kualitas pada keenam dimensi tersebut, terutama ketika volume dokumen yang harus diproses tinggi dan pekerjaan bersifat repetitif.

Penelitian empiris menunjukkan bahwa entri data manual memiliki tingkat kesalahan signifikan yang berkisar antara 0,55% hingga 3,6% per field, bahkan dapat mencapai 26,9% pada kondisi tertentu akibat faktor kelelahan dan distrase manusia (Mays dan Mathias, 2019; Barchard dkk., 2020). Fenomena ini menegaskan bahwa metode konvensional seperti visual checking menghasilkan risiko kesalahan yang jauh lebih tinggi dibandingkan pendekatan otomatis, sehingga mengancam integritas kualitas data organisasi secara keseluruhan. Tingkat kesalahan ini, meskipun tampak kecil pada skala individual, dapat mengakibatkan ketidakakuratan yang signifikan dalam laporan keuangan apabila tidak terdeteksi dan terkoreksi lebih awal. Selain itu, proses manual membutuhkan waktu pemrosesan yang jauh lebih lama dibandingkan dengan pendekatan otomatis, sehingga menjadi hambatan dalam alur kerja yang membutuhkan kecepatan tinggi.

Perkembangan teknologi telah mendorong evolusi pendekatan otomatisasi data entry dari rule-based Optical Character Recognition (OCR) tradisional, menuju sistem berbasis machine learning, hingga pendekatan terkini yang memanfaatkan Large Language Model (LLM) dan model multimodal. Keterbatasan

Page 28
<page_number>18</page_number>

OCR tradisional dalam menangani variasi layout dan kualitas gambar yang rendah menjadi pendorong utama adopsi pendekatan berbasis AI yang lebih adaptif dan dapat menggeneralisasi lintas format dokumen.

2.4 Large Language Models (LLM)

Large Language Models (LLM) didefinisikan sebagai model bahasa berbasis jaringan saraf dalam dengan jumlah parameter yang sangat besar, umumnya berkisar dari miliaran hingga ratusan triliun parameter, yang dilatih pada korpus teks berskala masif, dengan dibangun di atas arsitektur Transformer (Zhao dkk., 2026). Karakteristik utama LLM adalah kemampuan general-purpose language understanding and generation yang diperoleh melalui pelatihan miliaran parameter model pada data teks masif, sebagaimana diprediksi oleh scaling laws (Minaee dkk., 2025). Evolusi model bahasa dapat ditelusuri dari statistical language models, neural language models, pre-trained language models (PLMs), hingga LLM yang menunjukkan kemampuan khusus (special abilities) yang tidak ditemukan pada model dengan skala lebih kecil ketika skala parameter melampaui ambang batas tertentu.

Salah satu kemampuan utama LLM yang relevan untuk pengembangan sistem agentic adalah kemampuan instruction-following, yaitu kemampuan model untuk memahami dan mengeksekusi instruksi yang diberikan dalam bahasa alami (Wang dkk., 2025). Kemampuan ini memungkinkan LLM berperan sebagai mesin pengambil keputusan dalam sistem agent, menentukan langkah-langkah eksekusi yang perlu dilakukan untuk menyelesaikan tugas yang diberikan pengguna tanpa memerlukan pemrograman eksplisit untuk setiap skenario.

LLM modern juga memiliki kemampuan zero-shot dan few-shot generalization, di mana model dapat menangani tugas baru tanpa pelatihan ulang, hanya dengan diberikan contoh atau instruksi dalam konteks prompt (Brown dkk., 2020). Kemampuan ini sangat relevan dalam pengembangan sistem agent yang perlu menangani variasi input pengguna yang luas dan tidak terprediksi sepenuhnya.

Page 29
<page_number>19</page_number>

Dalam penelitian ini, LLM digunakan dalam dua peran yang berbeda. Pertama, sebagai model dasar untuk GLM-OCR yang kemudian diadaptasi melalui proses fine-tuning menggunakan data struk pembelian untuk tugas ekstraksi terstruktur. Kedua, sebagai model orkestrasi untuk Supervisor Agent, SQL Agent, Data Entry Team Agent, dan Guardrails menggunakan Gemini 3.1 Pro yang mengkoordinasikan seluruh alur kerja sistem.

2.5 Transformers
Arsitektur Transformer diperkenalkan oleh Vaswani dkk., 2023 sebagai model sequence-to-sequence yang sepenuhnya berbasis mekanisme attention, tanpa menggunakan rekurensi maupun konvolusi. Pendekatan ini menjadi terobosan fundamental dalam pemrosesan bahasa alami karena memungkinkan komputasi dependensi antar posisi secara paralel dengan jumlah operasi sekuensial yang konstan, berbeda dengan Recurrent Neural Networks (RNN) yang memerlukan O(n) operasi sekuensial. Keberhasilan Transformer pada tugas machine translation dengan pencapaian 28,4 BLEU pada WMT 2014 English-to-German dan 41,8 BLEU pada WMT 2014 English-to-French telah menjadikannya arsitektur dominan tidak hanya dalam pemrosesan bahasa alami, tetapi juga dalam computer vision, pemrosesan audio, dan berbagai disiplin ilmu lainnya (Lin dkk., 2022).

Arsitektur Transformer terdiri dari dua komponen utama, yaitu encoder dan decoder, yang masing-masing disusun dari tumpukan L blok identik. Setiap blok encoder tersusun dari dua sub-lapisan utama: modul multi-head self-attention dan jaringan position-wise feed-forward network (FFN). Pada setiap sub-lapisan tersebut, diterapkan koneksi residual (residual connection) yang diikuti oleh Layer Normalization untuk memfasilitasi pelatihan model yang lebih dalam. Secara formal, setiap blok encoder dapat dituliskan sebagai berikut.

H' = LayerNorm(SelfAttention(X) + X) (2.1) H = LayerNorm(FFN(H') + H') (2.2)

dengan SelfAttention(·) menyatakan modul self-attention, LayerNorm(·) menyatakan operasi layer normalization, X adalah keluaran dari lapisan

Page 30
<page_number>20</page_number>

sebelumnya, H' adalah keluaran sub-lapisan attention, dan H adalah keluaran akhir blok encoder.

Blok decoder memiliki struktur yang serupa dengan blok encoder, namun dengan penambahan sub-lapisan ketiga berupa modul cross-attention yang ditempatkan di antara modul self-attention dan FFN. Modul cross-attention ini memungkinkan setiap posisi pada decoder untuk mengakses seluruh posisi pada keluaran encoder. Selain itu, modul self-attention pada decoder dimodifikasi dengan mekanisme masking untuk mencegah setiap posisi mengakses informasi dari posisi-posisi berikutnya, sehingga prediksi untuk posisi i hanya bergantung pada keluaran yang telah diketahui pada posisi kurang dari i. Mekanisme ini sering disebut sebagai autoregressive atau causal attention. Arsitektur keseluruhan Transformer yang terdiri dari encoder (kiri) dan decoder (kanan) dengan komponen multi-head attention, feed-forward network, residual connection, dan layer normalization, ditunjukkan pada Gambar 2.1.

<img>Diagram of Transformer Architecture</img>

Gambar 2.1 Arsitektur Transformer (Vaswani dkk., 2023)

Secara umum, arsitektur Transformer dapat digunakan dalam tiga cara, yaitu encoder-decoder untuk pemodelan sequence-to-sequence seperti machine translation, encoder only untuk tugas klasifikasi atau pelabelan sekuens seperti

Page 31
<page_number>21</page_number>

yang digunakan pada BERT, dan decoder only untuk pembangkitan sekuens seperti pemodelan bahasa pada keluarga GPT.

Komponen inti Transformer adalah mekanisme Multi-Head Self-Attention yang memungkinkan model memperhatikan bagian-bagian berbeda dari input secara simultan dan dari berbagai perspektif representasi. Secara formal, operasi attention dihitung sebagai berikut.

Attention(Q, K, V) = softmax($\frac{QK^T}{\sqrt{D_k}}$)V = AV (2.3)

dengan N dan M menyatakan panjang queries dan keys (atau values), Dk dan Dv menyatakan dimensi keys (atau queries) dan values, serta A = softmax($\frac{QK^T}{\sqrt{D_k}}$) yang disebut sebagai matriks attention. Fungsi softmax diterapkan secara baris (row-wise). Pembagian hasil dot-product dengan $\sqrt{D_k}$ dilakukan untuk mengatasi masalah vanishing gradient pada fungsi softmax, karena untuk nilai Dk yang besar, hasil dot-product memiliki magnitudo yang besar sehingga mendorong fungsi softmax ke wilayah dengan gradien yang sangat kecil.

Pemahaman arsitektur Transformer relevan dalam konteks penelitian ini karena teknik fine-tuning Low-Rank Adaptation (LoRA) yang digunakan bekerja secara langsung pada lapisan-lapisan linear dalam arsitektur Transformer. LoRA menambahkan matriks bobot low-rank pada lapisan proyeksi attention Q dan V untuk mengadaptasi perilaku model ke domain spesifik tanpa memodifikasi seluruh parameter model yang sudah dilatih.

2.6 Instruction Fine-Tuning dan Parameter-Efficient Fine-Tuning

Perkembangan paradigma pemrosesan bahasa alami telah bergeser dari sekadar pembelajaran representasi bahasa universal menuju teknik adaptasi yang lebih presisi dan efisien. Meskipun pre-training memberikan fondasi pengetahuan yang luas, model bahasa berskala besar seringkali memerlukan fase penyesuaian tambahan agar dapat menyelaraskan (align) kemampuannya dengan instruksi spesifik pengguna serta batasan sumber daya komputasi (Qiu dkk., 2020). Dalam konteks ini, Instruction Fine-Tuning (IFT) dan Parameter-Efficient Fine-Tuning (PEFT) muncul sebagai metodologi kunci yang berfokus untuk peningkatan

Page 32
<page_number>22</page_number>

kemampuan model dalam mengikuti perintah kontekstual secara akurat dan optimasi yang memungkinkan adaptasi model pada tugas hilir dengan hanya memodifikasi sebagian kecil parameter model.

2.6.1 Instruction Fine-Tuning (IFT)
Instruction fine-tuning, yang juga dikenal sebagai supervised instruction fine-tuning, merupakan proses untuk meningkatkan kemampuan LLM dalam mengikuti instruksi spesifik dan menghasilkan respons yang diinginkan (Parthasarathy dkk., 2024). Berbeda dengan pre-training di mana LLM dilatih untuk menghasilkan satu kata pada satu waktu melalui penyelesaian teks (text completion), instruction fine-tuning berfokus pada menggunakan data berlabel yang dirancang untuk mengajarkan model mengikuti jenis instruksi tertentu secara akurat dan konsisten (Raschka, 2025).

Proses IFT mengoptimalkan model dengan meminimalkan cross-entropy loss (atau negative log-likelihood) antara distribusi token yang diprediksi model dengan respons target (Ouyang dkk., 2022; Wei dkk., 2022), yang didefinisikan sebagai.

$$ \mathcal{L}{IFT} = -\sum{t=1}^{T} \log P_{\theta}(y_t | x, y_{<t}) \quad (2.4) $$

di mana x adalah instruksi yang diberikan, y_t adalah token ke-t dari respons target, y_{<t} adalah token respons sebelum posisi t, dan θ adalah parameter model yang dioptimalkan.

Motivasi penggunaan IFT dalam penelitian ini adalah adanya ketidaksesuaian antara output default GLM-OCR dengan skema JSON yang dibutuhkan sistem. Pada percobaan awal, GLM-OCR tanpa fine-tuning menghasilkan output yang tidak konsisten dalam format field, menggunakan nama field yang berbeda dari skema yang ditetapkan, dan melewatkan sejumlah field yang seharusnya diisi meskipun informasinya tersedia dalam gambar. Melalui IFT, model diajarkan untuk selalu menghasilkan output yang sesuai dengan skema ekstrasi yang sudah didefinisikan.

Page 33
<page_number>23</page_number>

2.6.2 Low-Rank Adaptation (LoRA)
Low-Rank Adaptation (LoRA) merupakan teknik Parameter-Efficient Fine-Tuning (PEFT) yang diperkenalkan oleh Hu dkk., (2021) sebagai solusi untuk permasalahan computational cost yang tinggi pada full fine-tuning LLM berskala besar dengan cara membekukan bobot model pre-trained dan menyuntikkan matriks dekomposisi rank rendah yang dapat dilatih ke dalam setiap lapisan arsitektur Transformer. LoRA memungkinkan adaptasi model pra-latih ke domain spesifik dengan jumlah parameter yang dapat dilatih jauh lebih sedikit, tanpa mengorbankan kualitas adaptasi secara signifikan.

Ide dasar LoRA berangkat dari hipotesis bahwa pembaruan bobot yang diperlukan selama fine-tuning memiliki rank intrinsik yang rendah. Dengan kata lain, perubahan yang dibutuhkan untuk mengadaptasi model ke tugas baru dapat direpresentasikan dalam ruang berdimensi rendah. Alih-alih memperbarui seluruh matriks bobot $W_0 \in \mathbb{R}^{d \times k}$, LoRA membekukan bobot asli dan menambahkan dekomposisi low-rank yang dapat dilatih.

$$ W' = W + \Delta W = W + BA \quad (2.5) $$

di mana $B \in \mathbb{R}^{d \times r}$ dan $A \in \mathbb{R}^{r \times k}$ dengan rank $r \ll \min(d, k)$. Selama proses fine-tuning, hanya matriks A dan B yang dilatih sementara bobot asli W tetap dibekukan. Matriks A diinisialisasi menggunakan distribusi acak Gaussian dan matriks B diinisialisasi dengan nilai nol, sehingga pada awal pelatihan $\Delta W = 0$ yang menjamin perilaku model pada tahap awal identik dengan model dasar. Sehingga output akhir lapisan dengan LoRA dihitung sebagai berikut.

$$ h = W_0x + \Delta Wx = W_0x + BAx \quad (2.6) $$

dengan $B \in \mathbb{R}^{d \times r}$ dan $A \in \mathbb{R}^{r \times k}$ adalah matriks dekomposisi rank rendah dengan rank $r \ll \min(d, k)$, $W_0$ dibekukan dan tidak menerima pembaruan gradien, sedangkan A dan B merupakan parameter yang dapat dilatih. Matriks A diinisialisasi dengan distribusi Gaussian acak dan B diinisialisasi dengan nol, sehingga $\Delta W = BA$ bernilai nol pada awal pelatihan. Keluaran $\Delta Wx$ kemudian diskalakan dengan $\frac{\alpha}{r}$, di mana $\alpha$ adalah konstanta terhadap r. Pada gambar Gambar 2.2 menunjukan

Page 34
<page_number>24</page_number>

ilustrasi reparameterisasi LoRA yang menunjukkan matriks bobot pre-trained W₀ yang dibekukan dan matriks dekomposisi low-rank A dan B yang dapat dilatih.

<img>Illustration of LoRA reparameterization. It shows a pre-trained weight matrix W ∈ R^(d×d) being decomposed into a low-rank matrix A = N(0, σ²) and a zero matrix B = 0. The input x is multiplied by the low-rank matrix A, and the result is added to the pre-trained weights W, producing the output h.</img>

Gambar 2.2 Ilustrasi reparameterisasi LoRA (Hu dkk., 2021)

Keunggulan utama LoRA terletak pada efisiensi parameter yang signifikan. Sebagai ilustrasi, untuk model dengan dimensi d = 4096 dan rank r = 16, LoRA hanya memerlukan sekitar 0,1% jumlah parameter yang perlu dilatih dibandingkan full fine-tuning pada lapisan yang sama. Efisiensi ini memungkinkan fine-tuning dilakukan pada perangkat dengan kapasitas memori GPU yang terbatas dan mempercepat proses pelatihan secara keseluruhan.

Dalam penelitian ini, LoRA diterapkan pada lapisan proyeksi Q dan V dari mekanisme Multi-Head Attention pada model GLM-OCR. Pemilihan rank r dilakukan melalui serangkaian eksperimen untuk menemukan keseimbangan optimal antara kapasitas adaptasi model dan efisiensi komputasi yang tersedia.

2.6.3 LLAMA Factory
LLAMA Factory merupakan sebuah kerangka kerja (framework) terpadu yang dirancang untuk memfasilitasi proses fine-tuning yang efisien terhadap lebih dari 100 model bahasa besar (LLM). Dikembangkan oleh (Zheng dkk., 2024), framework ini mengintegrasikan berbagai teknik adaptasi model terkini ke dalam satu sistem yang skalabel, memungkinkan pengembang untuk melakukan instruction tuning tanpa perlu membangun infrastruktur pelatihan dari awal. Arsitektur LLAMA Factory memisahkan komponen manajemen data, pemilihan

Page 35
<page_number>25</page_number>

model, dan algoritma optimasi, sehingga memberikan fleksibilitas tinggi dalam mengelola alur kerja pelatihan model secara sistematis dan terstandarisasi, yang dapat ditunjukan pada Gambar 2.3.

<img>LLaMA Factory Architecture Diagram</img>

Gambar 2.3 Arsitektur LLaMA Factory (Zheng dkk., 2024)

Efisiensi yang ditawarkan oleh LLaMA Factory terletak pada kemampuannya untuk menggabungkan teknik PEFT, seperti LoRA, dengan optimasi memori tingkat lanjut, di mana fitur-fitur yang dimanfaatkan mencakup dukungan native untuk model multimodal dan integrasi format dataset percakapan yang kompleks. Fitur-fitur LLaMA Factory yang dimanfaatkan dalam penelitian ini mencakup dukungan native untuk model GLM-OCR sebagai model multimodal, integrasi format dataset percakapan multimodal yang mencakup pasangan gambar dan teks, implementasi LoRA dengan konfigurasi target modul yang fleksibel, serta monitoring metrik pelatihan dan validasi secara real-time.

2.7 Vision Language Model (VLM)

Vision Language Model (VLM) merupakan kelas model kecerdasan buatan yang dirancang untuk secara bersama memproses dan memahami informasi visual dan tekstual (Zhang dkk., 2024). Berbeda dari model tradisional yang menangani gambar atau teks secara independen, VLM dilatih pada dataset yang memasangkan gambar dengan keterangan, deskripsi, atau bentuk teks lainnya, sehingga mampu menjembatani kesenjangan antara persepsi visual dan pemahaman bahasa.

Page 36
<page_number>26</page_number>

Kemampuan ini memungkinkan VLM untuk melakukan berbagai tugas multimodal seperti image captioning, visual question answering (VQA), pengambilan berbasis teks (text-based retrieval), dan pembangkitan dialog berbasis gambar (image-grounded dialogue generation) (Verbovskiy, 2025).

Arsitektur VLM modern umumnya terdiri dari tiga komponen utama (Liu dkk., 2023). Komponen pertama adalah image encoder yang berfungsi mengekstraksi fitur visual dari gambar input ke dalam representasi berdimensi tinggi. Komponen kedua adalah language model (biasanya berupa LLM) yang berperan sebagai otak untuk pemrosesan semantik dan generasi teks. Komponen ketiga adalah connector atau projector yang berfungsi menjembatani perbedaan modalitas dengan memetakan fitur visual ke dalam ruang embedding yang dapat dipahami oleh language model. Contoh arsitektur VLM dapat diliat pada Gambar 2.4 yang merepresentasikan skema interaksi antara vision encoder, lapisan proyeksi, dan LLM dalam kerangka kerja LLaVA.

<img>Gambar 2.4 Contoh arsitektur VLM (H. Liu dkk., 2023)</img>

Kemampuan VLM dalam memahami dokumen visual seperti struk pembelian melampaui OCR tradisional dalam beberapa aspek yang kritis (Kim dkk., 2022). VLM dapat memahami konteks visual dokumen secara holistik, menghubungkan informasi yang tersebar di berbagai bagian dokumen, serta menangani ambiguitas teks dengan memanfaatkan pemahaman visual tentang tata letak dan struktur dokumen (Xu dkk., 2020; Mathew, Karatzas dan Jawahar, 2021). Kemampuan ini menjadikan VLM sebagai pilihan yang lebih tepat untuk tugas KIE dari dokumen semi-structured yang memiliki variasi layout tinggi dibandingkan dengan pendekatan berbasis aturan atau OCR tradisional.

Page 37
<page_number>27</page_number>

2.8 Visual Document Understanding (VDU)
Visual Document Understanding (VDU) merupakan bidang yang berkaitan dengan interpretasi dan pemahaman berbagai dokumen digital-natif atau hasil pemindaian, yang mencakup namun tidak terbatas pada formulir, tabel, laporan, dan makalah akademis. VDU secara fundamental bergantung pada kemampuan untuk mengekstraksi, mengenali, dan memahami informasi tekstual dan visual yang tertanam dalam dokumen, menjembatani kesenjangan antara dokumen fisik dan sistem digital. Berbeda dari tugas visi-bahasa konvensional, VDU secara khusus berkaitan dengan skenario yang kaya teks (text-rich scenarios) yang mengandung elemen dokumen yang berlimpah (X. Li dkk., 2024).

2.8.1 OCR Tradisional
Optical Character Recognition (OCR) merupakan teknologi yang digunakan untuk mengonversi berbagai jenis dokumen, seperti file kertas yang dipindai, dokumen PDF, atau gambar yang diambil oleh kamera digital, menjadi teks yang dapat diedit dan dicari. Dengan menganalisis bentuk dan pola karakter dalam suatu gambar, perangkat lunak OCR dapat mengekstraksi informasi tekstual dan membuatnya dapat digunakan untuk berbagai aplikasi, termasuk digitalisasi dokumen, otomasi entri data, dan pengambilan informasi (Verbovskiy, 2025).

Keterbatasan utama OCR tradisional dalam konteks pemrosesan struk pembelian terletak pada ketidakmampuannya memahami struktur semantik dokumen. OCR hanya menghasilkan teks mentah tanpa informasi tentang makna atau hubungan semantik antar elemen teks. Untuk mengekstrak informasi terstruktur dari output OCR tradisional, diperlukan tahapan lanjutan berupa Named Entity Recognition (NER) atau aturan berbasis ekspresi reguler yang tidak dapat menggeneralisasi dengan baik terhadap variasi format struk yang beragam.

Selain itu, akurasi OCR tradisional sangat bergantung pada kualitas gambar input. Foto struk dengan kondisi pencahayaan tidak merata, perspektif miring, resolusi rendah, atau teks yang tercetak pudar dapat menghasilkan output penuh kesalahan pengenalan karakter yang kemudian berdampak pada seluruh pipeline ekstraksi informasi hilirnya.

Page 38
<page_number>28</page_number>

2.8.2 VLM-Based Document Understanding
Pendekatan berbasis VLM untuk pemahaman dokumen mengatasi keterbatasan OCR tradisional dengan memproses dokumen secara end-to-end, menggabungkan pengenalan teks dan pemahaman semantik dalam satu proses inferensi model (Guan dkk., 2026). Model berbasis pendekatan ini dilatih untuk memahami tata letak dokumen sebagai bagian integral dari pemahaman semantiknya, bukan sebagai langkah pra-pemrosesan yang terpisah.

Keunggulan utama pendekatan ini adalah kemampuan generalisasi yang lebih baik terhadap variasi format dokumen, toleransi yang lebih tinggi terhadap noise dan distorsi gambar, serta kemampuan untuk langsung menghasilkan output terstruktur tanpa pipeline pemrosesan tambahan (Bai dkk., 2023). Dalam evaluasi pada dokumen bisnis, model berbasis VLM menunjukkan performa yang secara konsisten lebih tinggi dibandingkan pipeline OCR tradisional pada tugas KIE, khususnya untuk dokumen dengan layout yang kompleks dan bervariasi (Huang dkk., 2022).

2.8.3 General Language Model-OCR (GLM-OCR)
General Language Model-OCR merupakan model OCR multimodal kompak dengan 0,9 miliar parameter yang dirancang untuk pemahaman dokumen nyata secara menyeluruh. Model ini menggabungkan vision encoder CogViT berkapasitas 0,4 miliar parameter dengan language decoder GLM berkapasitas 0,5 miliar parameter, mencapai keseimbangan kuat antara efisiensi komputasi dan performa pengenalan (Duan, S. dkk., 2026). Dibangun di atas kerangka kerja encoder-decoder GLM-V (Hong, W. dkk., 2026) GLM-OCR mengatasi ketidakefisienan dekoding autoregressif standar pada tugas OCR yang bersifat deterministik melalui mekanisme Multi-Token Prediction (MTP) yang memprediksi beberapa token sekaligus per langkah, sehingga meningkatkan throughput dekoding secara signifikan. Pada tingkat sistem, pipeline dua tahap diadopsi di mana PP-DocLayoutV3 terlebih dahulu melakukan analisis tata letak, diikuti oleh pengenalan region secara paralel.

Page 39
<page_number>29</page_number>

Sebagaimana ditunjukkan pada Gambar 2.5, GLM-OCR mencapai skor 94,6 pada OmniDocBench V1.5, menempati peringkat pertama di antara seluruh model yang dievaluasi meskipun hanya memiliki 0,9 miliar parameter. Pencapaian ini mengonfirmasi bahwa arsitektur yang dirancang secara cermat dan efisien terhadap parameter mampu menandingi atau melampaui model berskala besar pada tugas pemrosesan dokumen yang kompleks.

<img>Bar chart comparing GLM-OCR with other models on OmniDocBench V1.5. The chart shows scores for GLM-OCR, PaddleOCR-VL-1.5, PaddleOCR-VL, MinerU2.5, Gemini-3 Pro, Qwen3-VL-235B-A22B, Gemini-2.5 Pro, MonkeyOCR-pro-3B, dots.ocr, MonkeyOCR-3B, Qwen2.5-VL-72B, Deepseek-OCR, MonkeyOCR-pro-1.2B, PP-StructureV3, MinerU2-VLM, GPT-5.2, Dolphin-1.5, MinerU2-pipeline, and Dolphin. The chart is divided into four sections: Overall Score, Text Score, Formula Score, and Reading Order Score. GLM-OCR achieves the highest score in all categories.</img>

Gambar 2. 5 Performa GLM-OCR pada OmniDocBench V1.5 dibandingkan dengan model-model lain (Duan, S. dkk., 2026).

Arsitektur GLM-OCR
Sebagaimana diilustrasikan pada Gambar 2.6, sistem GLM-OCR berpusat pada GLM-OCR Core yang mengikuti paradigma vision-language generative. Model inti terdiri dari dua komponen utama. Komponen pertama adalah Vision Encoder (CogViT, 400 juta parameter) yang bertanggung jawab mengekstraksi representasi visual tingkat tinggi dari citra dokumen. Komponen kedua adalah LLM Decoder (GLM, 500 juta parameter) yang merupakan model bahasa autoregressif yang menghasilkan keluaran teks terstruktur yang dikondisikan pada embedding visual dan prompt tekstual. Fitur visual yang dihasilkan encoder diproyeksikan ke

Page 40
<page_number>30</page_number>

dalam ruang embedding bahasa dan dimasukkan ke dalam decoder sebagai token prefiks.

Kerangka kerja ini mendukung dua tugas utama dalam formulasi generatif yang terpadu. Tugas 1 adalah Document Parsing, di mana pipeline terlebih dahulu melakukan analisis tata letak menggunakan PP-DocLayoutV3 yang mendekomposisi dokumen menjadi region-region yang koheren secara semantik, kemudian setiap region diproses secara independen oleh GLM-OCR Core, dan keluaran regional yang dihasilkan diagregasi oleh modul Merge and Post Process untuk menghasilkan keluaran terstruktur dalam format Markdown dan JSON. Tugas 2 adalah Key Information Extraction, di mana citra dokumen penuh dimasukkan langsung ke GLM-OCR bersama prompt tekstual spesifik-tugas tanpa bergantung pada pemotongan tata letak eksplisit, sehingga model belajar memperhatikan region visual yang relevan secara implisit di bawah panduan prompt.

<img>Gambar 2. 6 Arsitektur keseluruhan dan alur kerja kerangka GLM-OCR (Duan, S. dkk., 2026)</img>

Arsitektur GLM-V
Keluarga model GLM-V menggunakan AIMv2-Huge sebagai inisialisasi vision encoder. Untuk memungkinkan ViT (Vision Transformer) mendukung resolusi gambar dan rasio aspek yang arbitrer, dua adaptasi diperkenalkan. Pertama, 2D-RoPE diintegrasikan ke dalam lapisan self-attention ViT, memungkinkan model untuk memproses gambar dengan rasio aspek ekstrem (lebih dari 200:1) atau resolusi tinggi (di atas 4K). Kedua, position embedding absolut yang dapat

Page 41
<page_number>31</page_number>

dipelajari dari ViT pre-trained dipertahankan dan diadaptasi secara dinamis ke masukan resolusi variabel melalui interpolasi bikubik. Untuk patch masukan pada grid Hp × Wp, koordinat integer g = (w, h) dari setiap patch dinormalisasi ke grid kontinu gnr yang mencakup [−1,1]:

gnr = (wnorm, hnorm) = 2 · ( (w + 0.5) / Wp, (h + 0.5) / Hp ) − 1 (2.7)

Koordinat yang telah dinormalisasi kemudian digunakan untuk mengambil sampel dari tabel position embedding asli Porig menggunakan fungsi interpolasi bikubik Ibicubic guna menghasilkan embedding posisi yang telah diadaptasi Padapted:

Padapted(g) = Ibicubic(Porig, gnorm) (2.8)

Seperti pada Gambar 2.7 yang menunjukkan arsitektur GLM-V yang terdiri dari tiga komponen yaitu ViT encoder untuk memproses dan mengkodekan gambar dan video, MLP projector untuk menyelaraskan fitur visual ke token tekstual, dan LLM sebagai language decoder untuk memproses token multimodal.

<img>Gambar 2.7 Arsitektur model GLM-V (Hong, W. dkk., 2026)</img>

Multi-Token Prediction (MTP)
GLM-OCR memperkenalkan loss Multi-Token Prediction (MTP) untuk meningkatkan efisiensi pelatihan dan akurasi pengenalan. Berbeda dari pemodelan bahasa standar yang mempelajari prediksi next-token dengan objektif cross-entropy L1 = −Σt log Pθ(xt+1 | xt:1), MTP menggeneralisasi pendekatan ini dengan menginstruksikan model untuk memprediksi n token masa depan secara bersamaan di setiap posisi dalam korpus pelatihan:

Page 42
<page_number>32</page_number>

$$ L_n = - \sum_t \log P_\theta(x_{t+n:t+1} | x_{t:1}) \quad (2.9) $$

Model ini menggunakan trunk bersama untuk menghasilkan representasi laten $z_{t:1}$ dari konteks yang diamati $x_{t:1}$, yang kemudian dimasukkan ke dalam n head keluaran independen untuk memprediksi secara paralel setiap token masa depan:

$$ P_\theta(x_{t+i} | x_{t:1}) = \text{softmax}\left(f_u\left(f_{h_i}(f_s(x_{t:1}))\right)\right) \quad (2.10) $$

untuk $i = 1, ..., n$, dengan $f_s$ adalah Transformer trunk bersama, $f_{h_i}$ adalah lapisan transformer head keluaran ke-i, dan $f_u$ adalah matriks unembedding bersama. Pendekatan MTP mengurangi diskrepansi distribusional antara teacher forcing pada saat pelatihan dan pembangkitan autoregressif pada saat inferensi, serta secara implisit memberikan bobot lebih tinggi pada token-token yang merupakan titik keputusan (choice points) yang berkorelasi erat dengan kelanjutan teks. Eksperimen menunjukkan bahwa model prediksi 4-token memecahkan 12% lebih banyak masalah pada HumanEval dan 17% lebih banyak pada MBPP dibandingkan model next-token yang sebanding, dan inferensi dapat dipercepat hingga 3× melalui self-speculative decoding (Gloeckle dkk., 2024).

Reinforcement Learning untuk OCR
GLM-OCR menerapkan reinforcement learning (RL) yang stabil untuk seluruh tugas guna meningkatkan generalisasi. Proses RL menggunakan GRPO (Group Relative Policy Optimization) sebagai algoritma optimisasi dan merancang sistem reward spesifik-domain untuk setiap subdomain multimodal. Untuk domain OCR secara khusus, desain reward menggunakan edit distance yang diformulasikan pada persamaan 2.11.

$$ \text{reward}{\text{OCR}} = 1 - \frac{d{\text{edit}}(\text{ans}, \text{gt})}{\max(|\text{ans}|, |\text{gt}|)} \quad (2.11) $$

dengan $d_{\text{edit}}(\text{ans}, \text{gt})$ adalah jarak edit antara jawaban model dan ground truth, $|\text{ans}|$ dan $|\text{gt}|$ masing-masing adalah panjang jawaban dan ground truth. Selain itu, GLM-OCR menggunakan Reinforcement Learning with Curriculum Sampling (RLCS) yang menerapkan wawasan curriculum learning pada pengambilan sampel daring. RLCS menggunakan kurikulum adaptif yang secara kontinu menyesuaikan

Page 43
<page_number>33</page_number>

tingkat kesulitan sampel pelatihan untuk mencocokkan kemampuan model yang terus berkembang, memastikan setiap pembaruan memberikan informasi yang maksimal.

Pipeline Analisis Dokumen
Untuk pemrosesan dokumen end-to-end, GLM-OCR dikombinasikan dengan PP-DocLayoutV3 untuk analisis tata letak dan pengenalan paralel. PP-DocLayoutV3 merupakan evolusi arsitektural signifikan yang bertransisi dari deteksi persegi panjang standar ke kerangka segmentasi instansi yang robust, sambil secara simultan mengintegrasikan prediksi urutan baca (reading order prediction) ke dalam arsitektur Transformer terpadu secara end-to-end (Cui dkk., 2026). Model ini memprediksi mask yang presisi pada tingkat piksel untuk elemen tata letak, yang krusial untuk mengisolasi komponen dokumen dalam skenario non-ideal seperti halaman miring atau melengkung. Urutan baca diturunkan dari skor presedens berpasangan (pairwise precedence score) Si,j yang dihitung dari query embedding yang telah diperhalus melalui global pointer mechanism:

Si,j = $\frac{f(q_i, q_j) - f(q_j, q_i)}{\sqrt{d_h}}$, di mana f(qi, qj) = (Wqqi)T(Wkqj) (2.12)

dengan Wq, Wk ∈ Rd×dh adalah matriks proyeksi yang dapat dipelajari dan dh menyatakan dimensi tersembunyi. Matriks relasi yang dihasilkan S ∈ RN×N bersifat anti-simetris (Si,j = -Sj,i), di mana Si,j > 0 mengimplikasikan elemen i mendahului elemen j. Urutan baca akhir ditentukan melalui strategi Voting-based Ranking yang mengurutkan elemen berdasarkan total suara presedens absolut Vj = Σi=1, i≠jN σ(Si,j). Seperti yang ditunjukkan Gambar 2.8 arsitektur dari PP-DocLayoutV3 bekerja.

<img>Diagram showing the architecture of PP-DocLayoutV3. The top part shows the input document, processed by a backbone (PP-HGNetV2), then an encoder/decoder (Transformer Layers) to produce a bounding box with order. This is then postprocessed by class, box, mask, and order postprocesses. The bottom part shows the hidden feature being projected to logits matrix, which is then used to determine the relative order logits and the final reading order.</img>

Gambar 2.8 Arsitektur PP-DocLayoutV3 (Cui dkk., 2026)

Page 44
<page_number>34</page_number>

Performa dan Keungguan
GLM-OCR mencapai skor 94,62 pada OmniDocBench V1.5, menempati peringkat pertama secara keseluruhan, dan memberikan hasil state-of-the-art pada benchmark pemahaman dokumen utama, termasuk pengenalan rumus, pengenalan tabel, dan ekstraksi informasi. Dengan hanya 0,9 miliar parameter, GLM-OCR mendukung deployment melalui vLLM, SGLang, dan Ollama, secara signifikan mengurangi latensi inferensi dan biaya komputasi, menjadikannya ideal untuk layanan high-concurrency dan deployment di perangkat edge.

Model ini mendukung dua jenis skenario prompt yaitu pemrosesan dokumen (document parsing) untuk mengekstraksi konten mentah dengan tugas pengenalan teks, rumus, dan tabel, serta ekstraksi informasi (information extraction) untuk mengekstraksi informasi terstruktur dari dokumen sesuai skema JSON yang didefinisikan.

Tabel 2.1 Perbandingan model dalam parsing dokumen & ekstraksi

Benchmark	GLM-OCR	PaddleOCR-VL-1.5	Deepseek-OCR2	MinerU2.5	dots.ocr	Gemini-3-Pro	GPT-5.2
OmniDocBench v1.5	94,6	94,5	91,1	90,7	88,4	90,3	85,4
OCRBench (Text)	94,0	75,3	34,7	75,3	92,1	91,9	83,7
UniMERNet	96,5	96,1	85,8	96,4	90,0	96,4	90,5
PubTabNet	85,2	84,6	—	88,4	71,0	91,4	84,4
TEDS_TEST	86,0	83,3	—	85,4	62,4	81,8	67,6
Nanonets-KIE	93,7	—	—	—	—	95,2	87,5
Handwritten-Forms	86,1	—	—	—	—	94,5	78,2
Sumber: (Duan, S. dkk., 2026) Keterangan: Specialized VLM: GLM-OCR, PaddleOCR-VL-1.5, Deepseek-OCR2, MinerU2.5, dots.ocr. General VLM: Gemini-3-Pro, GPT-5.2.

Page 45
<page_number>35</page_number>

Tabel 2.2 Perbandingan model dalam skenario dunia nyata

Task	GLM-OCR	PaddleOCR-VL-1.5	Deepseek-OCR2	MinerU2.5	dots.ocr	Gemini-3-Pro	GPT-5.2
Code	84,7	75,8	82,1	82,9	80,8	86,9	84,4
Real-world Table	91,5	86,1	—	70,8	81,8	90,6	86,7
Handwriting	87,0	87,4	73,8	54,2	71,7	90,0	78,0
Multi-language	69,3	54,8	56,1	27,8	65,1	86,2	70,1
Seal	90,5	42,2	40,4	—	63,0	91,3	58,8
Receipt (KIE)	94,5	—	—	—	—	97,3	83,5
Sumber: (Duan, S. dkk., 2026) Keterangan: Specialized VLM: GLM-OCR, PaddleOCR-VL-1.5, Deepseek-OCR2, MinerU2.5, dots.ocr. General VLM: Gemini-3-Pro, GPT-5.2.

Tabel 2.3 Perbandingan model dalam kecepatan inferensi

Methods	Image Inputs (Pages / Sec)	PDF Inputs (Pages / Sec)
GLM-OCR	0,67	1,86
PaddleOCR-VL-1.5	0,39	1,22
Deepseek-OCR2	0,32	—
MinerU2.5	0,18	0,48
dots.ocr	0,10	—
Sumber: (Duan, S. dkk., 2026) Keterangan: Specialized VLM: GLM-OCR, PaddleOCR-VL-1.5, Deepseek-OCR2, MinerU2.5, dots.ocr.

Pada percobaan awal penelitian ini, GLM-OCR tanpa fine-tuning menunjukkan kemampuan ekstraksi teks yang memadai namun belum konsisten dalam mengikuti skema JSON yang telah didefinisikan. Model cenderung menggunakan nama field yang berbeda dari spesifikasi, menghilangkan field yang tidak terisi alih-alih mengisinya dengan nilai kosong, dan menghasilkan struktur JSON yang tidak sepenuhnya konsisten antar inferensi. Melalui proses IFT dengan

Page 46
<page_number>36</page_number>

LoRA menggunakan LLaMA Factory, model diadaptasi untuk menghasilkan output yang sesuai dengan ekstrasi skema yang telah ditetapkan.

2.9 Key Information Extraction
Key Information Extraction (KIE) merupakan subbidang dari visual document understanding yang merujuk pada tugas untuk mengekstrak informasi spesifik dan terstruktur dari dokumen semi-structured (Rombach dan Fettke, 2026). Pada dokumen visually-rich seperti struk pembelian, faktur, dan formulir bisnis, KIE menghadapi tantangan yang unik karena informasi tidak hanya terkandung dalam konten teks tetapi juga dalam tata letak visual dokumen secara keseluruhan (Huang dkk., 2019).

Dokumen struk pembelian termasuk dalam kategori Visually-Rich Document Understanding (VRDU) yang membutuhkan pemahaman terpadu antara konten tekstual dan struktur spasial dua dimensi (Z. Wang dkk., 2023). Pada kategori ini, posisi elemen teks dalam ruang dokumen membawa makna semantik yang setara pentingnya dengan konten teks itu sendiri (Xu dkk., 2020). Sebagai contoh, nilai numerik yang berada di kolom kanan sejajar dengan nama item merupakan harga item tersebut, sementara nilai numerik di baris terbawah dokumen dengan format yang berbeda merupakan grand total pembayaran.

Pendekatan berbasis VLM untuk KIE yang digunakan dalam penelitian ini memanfaatkan kemampuan model untuk memahami hubungan spasial dan semantik secara simultan dalam satu inferensi. Dengan memberikan gambar dokumen dan skema JSON target sebagai instruksi, model secara langsung menghasilkan output terstruktur tanpa memerlukan tahapan segmentasi dokumen atau pemrosesan pipeline yang terpisah-pisah.

2.10 Agentic AI
Agentic AI merupakan sebuah paradigma baru dalam kecerdasan buatan yang mengacu pada sistem otonom yang dirancang untuk mencapai tujuan-tujuan kompleks dengan intervensi manusia yang minimal. Berbeda dengan AI tradisional yang bergantung pada instruksi terstruktur dan pengawasan ketat, Agentic AI mendemonstrasikan kemampuan adaptasi, pengambilan keputusan tingkat lanjut,

Page 47
<page_number>37</page_number>

dan kemandirian operasional, sehingga memungkinkannya beroperasi secara dinamis dalam lingkungan yang terus berkembang. Era Agentic AI (2022–sekarang) merupakan era terkini di mana kemampuan generatif LLM dimanfaatkan untuk aksi dan otonomi, ditandai dengan kemunculan AI Agent seperti AutoGPT yang dapat mengejar tujuan melalui perencanaan dan penggunaan alat (tool use), yang kemudian berkembang menjadi sistem multi-agen yang lebih kompleks (Abou Ali, Dornaika dan Charafeddine, 2025).

2.10.1 AI Agent
AI Agent merupakan sistem berbasis LLM yang dilengkapi dengan kemampuan untuk merencanakan, memutuskan, dan mengeksekusi serangkaian tindakan secara otonom untuk mencapai tujuan yang ditetapkan (L. Wang dkk., 2023). Berbeda dengan penggunaan LLM sebagai komponen reaktif, AI agent bersifat proaktif dalam berinteraksi dengan lingkungan eksternal secara iteratif (Xi dkk., 2023).

Menurut Sapkota dkk., (2026), AI Agent dapat dibedakan dari Agentic AI melalui karakteristik berikut: AI agent merupakan sistem modular yang didorong dan diaktifkan oleh LLM untuk otomatisasi tugas spesifik, dengan kemampuan melakukan tool integration, prompt engineering, dan peningkatan reasoning. Sementara itu, Agentic AI merepresentasikan pergeseran paradigma yang ditandai oleh kolaborasi multi-agen, dekomposisi tugas dinamis, memori persisten, dan otonomi yang terkoordinasi.

Komponen utama AI Agent terdiri dari empat elemen fungsional. Elemen pertama adalah profil yang mendefinisikan peran, kemampuan, dan batasan agent. Elemen kedua adalah memori yang menyimpan konteks percakapan dan informasi sesi. Elemen ketiga adalah perencanaan yang memungkinkan agent mendekomposisi tugas kompleks menjadi langkah-langkah yang dapat dieksekusi secara berurutan. Elemen keempat adalah aksi yang memungkinkan agent berinteraksi dengan lingkungan eksternal melalui pemanggilan tool yang terdefinisi (Acharya dkk., 2025).

Page 48
<page_number>38</page_number>

Dalam penelitian ini, AI Agent diimplementasikan sebagai Supervisor Agent bernama Klaudia yang bertugas memahami permintaan pengguna, mengorkestrasikan alur kerja pemrosesan struk, dan mendelegasikan tugas ke sub-agent yang sesuai berdasarkan kebutuhan pada setiap giliran percakapan.

2.10.2 Multi Agent System (MAS)

Multi-Agent System (MAS) merupakan arsitektur yang terdiri dari beberapa AI Agent yang berkolaborasi untuk menyelesaikan tugas kompleks yang tidak efisien atau tidak praktis apabila diselesaikan oleh satu agent tunggal. Setiap agent dalam MAS memiliki spesialisasi, konteks sistem, dan himpunan tool yang berbeda, dan berinteraksi melalui mekanisme komunikasi yang terdefinisi (Gao dkk., 2025).

Keunggulan utama MAS dibandingkan pendekatan single-agent adalah kemampuan untuk menerapkan prinsip separation of concerns, di mana setiap agent dapat difokuskan pada domain yang spesifik sehingga kompleksitas sistem dapat dikelola dengan lebih baik (Biswas dkk., 2025). Keunggulan MAS atas sistem single-agent telah terdokumentasi secara empiris, di mana sistem multi-agent menunjukkan rata-rata peningkatan performa sebesar 21,3% dibandingkan model foundation tunggal, dengan peningkatan terbesar pada domain yang memerlukan penalaran logis langkah-demi-langkah (31,7%) dan analisis multi-perspektif (28,4%). Selain itu, pendekatan kolaboratif menggunakan critic dan refinement agents mencapai peningkatan 26% dalam akurasi pengambilan fakta sekaligus mengurangi halusinasi sebesar 41% dibandingkan pendekatan single-agent tradisional (Mohan Singh, 2025). Studi Sreedhar dan Chilton, (2024) secara khusus mengungkapkan bahwa sistem multi-agent lebih akurat daripada LLM tunggal (88% vs. 50%) dalam mensimulasikan penalaran dan aksi manusia untuk pasangan kepribadian tertentu. Dalam eksperimen pada ultimatum game, sistem multi-agent mencapai gameplay yang konsisten dengan data eksperimental manusia dalam 85% simulasi, sementara LLM tunggal hanya mencapai 50%.

Dalam penelitian ini, MAS diimplementasikan dengan pembagian tanggung jawab yang jelas antara Supervisor Agent untuk orkestrasi dan percakapan, SQL

Page 49
<page_number>39</page_number>

Agent untuk operasi pembacaan database, dan Data Entry Team yang terdiri dari agen-agen yang bertugas membaca, memodifikasi, dan menulis ke Google Sheets.

2.10.3 Hierarchical Agent Teams

Hierarchical agent teams (tim agen hierarkis) merupakan pola arsitektur MAS di mana agent-agent diorganisasi dalam struktur hierarkis dengan Supervisor Agent yang mengkoordinasikan pekerjaan sub-agent yang lebih terspesialisasi. Pendekatan ini terinspirasi dari cara seorang konduktor mengorkestrasi simfoni, di mana planning agent pusat mengurai tujuan kompleks dan mendelegasikan sub-tugas kepada tim agent spesialis (Zhang dkk., 2026). Pola ini diimplementasikan menggunakan LangGraph, yaitu framework ekstensi dari LangChain yang memungkinkan pembuatan alur agent sebagai state machine yang dapat dikontrol secara deterministik. Pada Gambar 2.9 menunjukkan contoh implementasi hierarchical agent teams dengan planning agent sebagai orchestrator dan specialized sub-agents.

<img>Gambar 2.9 Contoh arsitektur hierarchical agent teams (W. Zhang dkk., 2026)</img>

Dibandingkan dengan arsitektur flat (non-hierarkis), tim agent hierarkis menawarkan keunggulan struktural berupa kemampuan dekomposisi tugas yang lebih efisien karena planning agent memiliki perspektif global, spesialisasi yang lebih tajam karena setiap sub-agent dioptimalkan untuk domain tertentu, serta

Page 50
<page_number>40</page_number>

skalabilitas yang lebih baik karena penambahan kapabilitas baru cukup dilakukan dengan menambahkan sub-agent baru tanpa mengubah arsitektur inti.

Dalam pola ini, supervisor atau sebagai planing agent menerima permintaan dari pengguna, mengevaluasi kebutuhan tugas, dan mendelegasikan pekerjaan ke sub-agent yang paling sesuai. Sub-agent mengeksekusi tugas spesifik menggunakan tools yang tersedia, mengembalikan hasilnya ke supervisor, yang kemudian mengintegrasikan hasil tersebut dan merespons pengguna dengan informasi yang komprehensif.

LangGraph digunakan untuk mendefinisikan state graph yang merepresentasikan alur percakapan dan eksekusi tugas sebagai sebuah graf terarah. Node dalam graf merepresentasikan agent atau proses tertentu, sementara edge merepresentasikan transisi kondisional berdasarkan output agent. Mekanisme interrupt bawaan LangGraph memungkinkan implementasi human-in-the-loop pada titik-titik kritis dalam alur eksekusi yang membutuhkan konfirmasi manusia sebelum tindakan irreversible dilakukan (LangChain, 2026).

2.11 HITL (Human in the Loop)

Human-in-the-Loop (HITL) merupakan paradigma sistem AI di mana manusia dilibatkan secara aktif dalam proses pengambilan keputusan sistem, terutama pada titik-titik kritis yang membutuhkan validasi, koreksi, atau persetujuan eksplisit sebelum sistem melanjutkan ke tahap berikutnya (Natarajan dkk., 2024).

Dalam konteks sistem agentic berbasis LLM, HITL sangat relevan untuk menangani skenario di mana output model bersifat non-deterministik, terdapat ambiguitas dalam instruksi pengguna, atau tindakan yang akan dieksekusi bersifat irreversible (Atil dkk., 2025). Penulisan data ke database atau spreadsheet adalah contoh operasi irreversible yang apabila dilakukan berdasarkan ekstraksi yang salah akan menghasilkan data corruption yang sulit diperbaiki. Keterlibatan manusia di titik-titik ini secara langsung mengurangi risiko silent data corruption yang tidak terdeteksi.

Page 51
<page_number>41</page_number>

Implementasi HITL dalam LangGraph dilakukan melalui mekanisme interrupt yang memungkinkan eksekusi graf dihentikan sementara pada node tertentu untuk menunggu konfirmasi atau input koreksi dari pengguna. Setelah pengguna memberikan respons, eksekusi dilanjutkan dari titik yang sama dengan membawa informasi tambahan dari pengguna sebagai bagian dari konteks state yang diperbarui. Pada Gambar 2.10 menunjukkan skema arsitektur penerapan HITL pada agentic AI.

<img>Flowchart showing the HITL process. It starts with an Agent, which leads to a decision node "Interrupt?". If "no", it goes to "Execute". If "yes", it goes to a "Human" decision node. From "Human", it can go to "Execute" (via "approve") or "Cancel" (via "reject"). The "Execute" and "Cancel" nodes both lead back to the "Agent" node.</img>

Gambar 2.10 Arsitektur HITL pada sistem Agentic AI berbasis LangGraph (LangChain, 2026)

Dalam penelitian ini, HITL diimplementasikan sebagai checkpoint konfirmasi sebelum operasi penulisan data ke Google Sheets dieksekusi. Setelah Supervisor Agent memverifikasi data hasil ekstraksi bersama pengguna, pengguna diberikan kesempatan untuk meninjau, mengkonfirmasi, atau mengoreksi data sebelum Data Entry Team menjalankan operasi penulisan melalui MCP-GSheets. Keunggulan kritis HITL dalam konteks data entry adalah kemampuannya untuk mengatasi hallucination dan ambiguitas yang mungkin terjadi ketika agent memproses dokumen dengan kualitas rendah atau format yang tidak lazim. Alih-alih membiarkan agent secara otonom memasukkan data yang berpotensi salah ke dalam sistem, mekanisme HITL menyediakan checkpoint terstruktur di mana pengguna dapat mengonfirmasi, memodifikasi, atau menolak hasil ekstraksi sebelum aksi final dieksekusi.

2.12 MCP (Model Context Protocol)

Model Context Protocol (MCP) merupakan standar terbuka yang mendefinisikan protokol komunikasi dua arah yang terpadu dan dynamic discovery antara model AI dengan alat atau sumber daya eksternal, yang bertujuan untuk

Page 52
<page_number>42</page_number>

meningkatkan interoperabilitas dan mengurangi fragmentasi di berbagai sistem. MCP diperkenalkan oleh Anthropic pada akhir tahun 2024, terinspirasi dari Language Server Protocol (LSP), sebagai solusi atas fragmentasi yang terjadi dalam ekosistem integrasi tool pada aplikasi AI. MCP mendefinisikan antarmuka yang konsisten antara AI model sebagai client dan layanan eksternal sebagai server, sehingga integrasi antara model dengan berbagai kapabilitas eksternal dapat dilakukan secara modular, dapat dipertukarkan, dan tidak bergantung pada implementasi spesifik model tertentu (Hou dkk., 2025).

Arsitektur MCP terdiri dari tiga komponen utama. Komponen pertama adalah MCP Host, yaitu aplikasi yang menjalankan AI model dan mengelola komunikasi dengan MCP Server. Komponen kedua adalah MCP Client, yaitu modul dalam host yang mengelola koneksi dan protokol komunikasi ke server. Komponen ketiga adalah MCP Server, yaitu layanan yang mengekspos kapabilitas berupa tools, resources, dan prompts melalui antarmuka MCP yang terstandarkan.

Keunggulan utama penggunaan MCP dibandingkan integrasi tool secara langsung adalah pemisahan yang tegas antara logika AI (reasoning) dan eksekusi tool (action). Dalam prinsip “agent sebagai reasoning, tool sebagai execution”, MCP menjadi batas eksplisit yang memastikan seluruh operasi pada sumber data eksternal selalu melalui tool yang terdefinisi dengan kontrak yang jelas dan dapat diaudit, bukan melalui eksekusi kode arbitrer yang dihasilkan oleh model (Oribe, 2025).

Dalam penelitian ini, dua MCP Server diimplementasikan. MCP-SQLite menyediakan tool untuk operasi pembacaan database SQLite yang digunakan oleh SQL Agent untuk mengambil data dokumen, halaman, dan hasil ekstraksi. MCP-GSheets menyediakan tool untuk operasi pembacaan dan penulisan ke Google Sheets yang digunakan oleh Data Entry Team untuk membuat sheet, memperbarui sel, dan menambahkan baris data.

2.13 Prompt Engineering

Prompt engineering merupakan teknik yang tidak terpisahkan untuk memperluas kapabilitas LLM dan VLM melalui perancangan instruksi tugas-

Page 53
<page_number>43</page_number>

spesifik, yang dikenal sebagai prompt, untuk meningkatkan efektivitas model tanpa memodifikasi parameter inti model tersebut. Alih-alih memperbarui parameter model, prompt memungkinkan integrasi yang mulus dari model pre-trained ke dalam tugas-tugas downstream dengan hanya mengandalkan prompt yang diberikan untuk membangkitkan perilaku model yang diinginkan (Lamba, 2024).

Signifikansi prompt engineering terletak pada dampak transformatifnya terhadap adaptabilitas LLM dan VLM. Berbeda dengan paradigma tradisional di mana pelatihan ulang model atau fine-tuning ekstensif sering kali diperlukan untuk performa yang spesifik-tugas, prompt engineering memungkinkan model yang sama untuk menjalankan beragam tugas melalui desain instruksi yang cermat. Lanskap prompt engineering kontemporer mencakup spektrum teknik yang luas, mulai dari metode foundational seperti zero-shot dan few-shot prompting hingga pendekatan yang lebih kompleks seperti chain of thought dan ReAct prompting.

2.13.1 Zero Shot Prompting
Zero-shot prompting adalah teknik di mana model diberikan instruksi dan deskripsi tugas tanpa contoh eksplisit dalam prompt. Model mengandalkan pengetahuan dan kemampuan generalisasi yang diperoleh selama pre-training untuk memahami dan menyelesaikan tugas yang diminta. Dalam penelitian ini, zero-shot prompting diterapkan pada prompt GLM-OCR yang memberikan skema JSON target dan meminta model mengekstrak informasi dari gambar struk sesuai skema tersebut tanpa contoh referensi tambahan dalam prompt.

2.13.2 Few Shot Prompting
Few-shot prompting adalah teknik di mana model diberikan sejumlah kecil contoh pasangan input-output dalam prompt sebelum tugas yang sebenarnya diberikan. Contoh-contoh ini memberikan panduan kontekstual tentang format, gaya, dan kualitas output yang diharapkan. Dalam penelitian ini, few-shot prompting diterapkan pada system prompt agent untuk mendefinisikan pola respons dan format yang diinginkan dari Supervisor Agent dalam berinteraksi dengan pengguna.

Page 54
<page_number>44</page_number>

2.13.3 Chain of Thought Prompting
Chain-of-Thought (CoT) prompting adalah teknik yang mendorong model untuk menghasilkan langkah-langkah penalaran eksplisit secara berurutan sebelum memberikan jawaban atau tindakan akhir. CoT terbukti secara signifikan meningkatkan performa model pada tugas yang membutuhkan penalaran multi-langkah (Wei dkk., 2023). Dalam sistem ini, CoT diterapkan pada Supervisor Agent untuk memastikan proses analisis kebutuhan pengguna dan penentuan tindakan yang tepat dilakukan secara sistematis sebelum delegasi ke sub-agent dieksekusi.

2.13.4 ReAct Prompting
ReAct (Reasoning and Acting) adalah framework yang mengintegrasikan kemampuan penalaran (CoT) dengan kemampuan bertindak melalui penggunaan tool dalam satu alur inferensi yang terpadu (Yao dkk., 2023). Dalam framework ReAct, model beriterasi melalui siklus thought yang berisi penalaran tentang situasi saat ini, action yang berisi pemanggilan tool yang dipilih, dan observation yang berisi pemrosesan hasil tool untuk menentukan langkah selanjutnya. Siklus ini berulang hingga tugas dinyatakan selesai.

ReAct menjadi paradigma utama dalam implementasi seluruh agent pada penelitian ini. Setiap agent dalam sistem mengikuti siklus ReAct di mana model terlebih dahulu menganalisis konteks dan kebutuhan (thought), kemudian memilih dan memanggil tool yang sesuai melalui MCP (action), lalu memproses hasil tool untuk menentukan apakah tugas sudah selesai atau diperlukan langkah tambahan (observation).

2.13.5 Persona-based Prompting
Persona-based prompting atau role-play prompting adalah teknik perancangan instruksi yang menetapkan identitas, karakter, atau peran spesifik kepada model bahasa untuk mengatur nada bicara, perilaku, dan batasan operasionalnya. Menurut Shanahan dkk., (2023), pemberian persona memungkinkan model untuk mengadopsi kerangka berpikir tertentu yang konsisten, di mana model tidak hanya memproses informasi secara fungsional tetapi juga menyesuaikan gaya komunikasinya dengan profil yang diberikan. Teknik ini

Page 55
<page_number>45</page_number>

bekerja dengan cara membatasi ruang probabilitas respons model agar selaras dengan karakteristik sosiolinguistik dan kepakaran yang melekat pada peran tersebut, sehingga meningkatkan kepercayaan pengguna dan kejelasan interaksi.

Dalam penelitian ini, persona-based prompting diimplementasikan untuk membentuk identitas "Klaudia" sebagai asisten AI yang ahli dalam pemrosesan data struk belanja. Penggunaan persona ini berfungsi sebagai jangkar perilaku (behavioral anchor) yang memastikan agen tetap beroperasi dalam batas kapabilitasnya, seperti membedakan antara alur data otomatis ke database dan kebutuhan instruksi eksplisit untuk penginputan ke Google Sheets. Melalui pendefinisian persona yang ramah, efisien, dan proaktif, agen mampu memberikan ringkasan hasil pemrosesan serta klarifikasi permintaan ambigu dengan nada profesional, yang secara efektif menjembatani kesenjangan antara fungsi teknis ekstraksi data dan kebutuhan komunikasi pengguna yang intuitif.

2.14 Context Engineering

Context engineering adalah praktik merancang dan mengelola secara sistematis seluruh konteks yang disuplai ke LLM pada setiap giliran inferensi, dengan tujuan memaksimalkan relevansi, akurasi, dan konsistensi respons model. Berbeda dengan prompt engineering yang fokus pada perancangan instruksi tunggal, context engineering mencakup pengelolaan komprehensif seluruh informasi yang membentuk jendela konteks model, termasuk instruksi sistem, riwayat percakapan, hasil tool, dan informasi sesi yang relevan (Mei dkk., 2025).

Komponen konteks yang dikelola dalam penelitian ini mencakup instruksi persona dan kapabilitas Klaudia dalam system prompt, riwayat percakapan sesi yang diambil dari database untuk memberikan memori percakapan, informasi file yang telah diunggah dalam sesi aktif beserta status ekstraktornya, dan hasil observasi dari pemanggilan tool oleh sub-agent yang dikembalikan ke supervisor.

Implementasi context enrichment dalam penelitian ini dilakukan dengan menginjeksikan informasi tentang semua file aktif dalam sesi ke dalam system prompt Supervisor Agent pada setiap giliran percakapan. Informasi ini mencakup nama file, tipe dokumen, status ekstraksi, jumlah halaman, dan file ID yang dapat

Page 56
<page_number>46</page_number>

direferensikan oleh agent. Mekanisme ini memastikan Supervisor Agent selalu memiliki kesadaran penuh tentang konteks sesi saat ini tanpa perlu melakukan query database secara eksplisit pada setiap giliran.

2.15 Benchmark Agentic AI
Evaluasi performa sistem Agentic AI memerlukan benchmark yang mampu mengukur kemampuan-kemampuan khas yang membedakannya dari model bahasa konvensional, meliputi kemampuan penggunaan tool (tool use), perencanaan multi-langkah, penalaran jangka panjang (long-horizon reasoning), kolaborasi antar-agent, dan kemampuan untuk mempertahankan koherensi dalam konteks yang sangat panjang. Lanskap benchmark Agentic AI telah berevolusi dari pengujian pengetahuan berbasis pertanyaan tetap, menuju paradigma evaluasi yang interaktif dan dinamis yang mengukur kemampuan agentic secara lebih realistis.

2.15.1 τ²-Bench
τ²-Bench (Tau-Squared Bench) merupakan benchmark yang dirancang untuk mengevaluasi conversational AI agents dalam lingkungan dual-control, di mana baik agent AI maupun pengguna dapat menggunakan tool untuk berinteraksi dengan dunia bersama yang dinamis. Berbeda dengan benchmark konvensional yang mensimulasikan lingkungan single-control (di mana hanya agent AI yang dapat menggunakan tool sementara pengguna tetap sebagai penyedia informasi pasif), τ²-Bench mencerminkan skenario dunia nyata seperti dukungan teknis di mana pengguna perlu aktif berpartisipasi dalam memodifikasi state lingkungan bersama (Barres dkk., 2025).

Eksperimen pada τ²-Bench menunjukkan penurunan performa yang signifikan ketika agent beralih dari lingkungan tanpa-pengguna ke lingkungan dual-control, menyoroti tantangan dalam memandu aksi pengguna sebagai salah satu aspek yang paling menantang bagi sistem agent percakapan saat ini.

2.15.2 MCP-Atlas
MCP-Atlas adalah benchmark berskala besar untuk mengevaluasi kompetensi penggunaan tool (tool-use competency) dengan MCP server nyata,

Page 57
<page_number>47</page_number>

terdiri dari 36 MCP server nyata dan 220 tool yang mencakup 1.000 tugas yang dirancang untuk menilai kompetensi penggunaan tool dalam workflow multi-langkah yang realistis. MCP-Atlas mengatasi ketegangan yang persisten dalam benchmark MCP sebelumnya antara ketelitian evaluasi dan skalabilitas melalui tiga pilihan desain utama (Bandi dkk., 2026).

Setiap tugas dalam MCP-Atlas didefinisikan oleh empat komponen wajib yaitu berupa tool set configuration (subset terkontrol 10–25 tool yang diekspos ke agent per tugas, terdiri dari 3–7 target tool dan 5–10 distractor), prompt (permintaan bahasa alami single-turn yang memerlukan beberapa panggilan tool tanpa menyebutkan nama server atau tool secara eksplisit), reference trajectory (urutan minimal panggilan tool yang menyelesaikan tugas, digunakan untuk analisis diagnostik), dan claims list (sekumpulan klaim atomik yang dapat diverifikasi secara independen yang bersama-sama membentuk respons komprehensif). Hasil evaluasi pada model-model frontier mengungkapkan bahwa model terbaik mencapai tingkat kelulusan lebih dari 50%, dengan kegagalan utama terjadi pada tool usage (pemilihan server yang salah, kesalahan parameter, kesalahan urutan) dan task understanding (penghentian dini, sub-tujuan yang terlewat).

2.15.3 APEX-Agents

APEX-Agents (AI Productivity Index for Agents) adalah benchmark untuk menilai apakah AI Agent dapat mengeksekusi tugas lintas-aplikasi jangka panjang (long-horizon, cross-application tasks) yang dibuat oleh analis perbankan investasi, konsultan manajemen, dan pengacara korporat. APEX-Agents mensimulasikan lingkungan kerja nyata di mana agent harus menavigasi file dan tool yang realistis, dengan tugas-tugas yang rata-rata memerlukan 1–2 jam untuk diselesaikan oleh profesional berpengalaman (Vidgen dkk., 2026).

Pembangunan APEX-Agents dilakukan dalam tiga langkah utama. Pertama, tim profesional industri membuat dunia-dunia (worlds) yang kaya data, masing-masing berdasarkan skenario proyek unik, di mana mereka merencanakan pekerjaan, melakukan riset, dan menghasilkan deliverable berkualitas tinggi dari awal. Kedua, profesional membuat tugas-tugas yang realistis dan menantang

Page 58
<page_number>48</page_number>

menggunakan file-file dari dalam setiap dunia. Ketiga, agent diberikan akses ke setiap dunia untuk mengeksekusi tugas-tugas tersebut dengan semua data dan perangkat lunak yang sama dengan yang digunakan manusia.

APEX-Agents sangat relevan untuk mengevaluasi Supervisor Agent dalam konteks penelitian ini, yakni agent yang harus mengelola keseluruhan alur dari pembacaan OCR hingga finalisasi data ke dalam spreadsheet tanpa kehilangan fokus sepanjang proses. Benchmark ini cocok digunakan ketika ingin menguji apakah AI benar-benar siap untuk menggantikan atau membantu pekerjaan kantor yang memerlukan pemikiran kritis dan penalaran jangka panjang.

2.15.4 MRCR v2

MRCR v2 (Multi-Round Co-reference Resolution version 2) adalah benchmark evaluasi kemampuan long-context yang melampaui tugas retrieval sederhana, menguji kemampuan model untuk mensintesis beberapa bagian informasi yang tersebar di seluruh konteks secara berurutan dan koheren. Evaluasi ini merupakan bagian dari kerangka Michelangelo yang menggunakan Latent Structure Queries (LSQ) untuk menghasilkan evaluasi penalaran konteks panjang yang dapat diperluas secara arbitrer (Vodrahalli dkk., 2024).

Dalam tugas MRCR, model melihat percakapan panjang antara pengguna dan model, di mana pengguna meminta penulisan (misalnya puisi, teka-teki, esai) tentang topik-topik yang berbeda dan model memberikan respons. Tugas yang diberikan adalah mereproduksi output dari percakapan tersebut yang dihasilkan dari salah satu permintaan spesifik, di mana format atau topik atau keduanya, saling tumpang tindih untuk menciptakan kunci yang secara adversarial mirip satu sama lain. Model dinilai menggunakan metrik string-similarity antara output model dan respons yang benar.

MRCR dapat dipandang sebagai perluasan tugas needle-in-a-haystack (pencarian informasi spesifik dalam dokumen panjang) ke skenario di luar retrieval, yang mengharuskan model menggunakan informasi tentang urutan beberapa "jarum" yang ditempatkan dalam "tumpukan jerami" untuk menjawab kueri. Setup ini memiliki keunggulan menciptakan jarum-jarum yang sangat mirip (highly

Page 59
<page_number>49</page_number>

similar needles) yang harus diambil, sehingga mengharuskan model untuk menggunakan informasi dari dua tempat dalam konteks untuk menentukan jawaban yang benar.

2.15.5 Komparasi Performa Model Berdasarkan Benchmark

Evaluasi komprehensif berbagai model frontier pada benchmark Agentic AI memberikan gambaran yang jelas tentang kemampuan dan keterbatasan sistem-sistem terbaik saat ini. Google DeepMind, (2026) mempublikasikan hasil evaluasi Gemini 3.1 Pro yang mencakup beberapa benchmark utama Agentic AI yang telah dibahas sebelumnya. Tabel 2.4 menyajikan komparasi performa model-model frontier terkemuka pada benchmark-benchmark tersebut.

Tabel 2.4 Komparasi performa model-model frontier pada benchmark Agentic AI utama

Benchmark	Gemini 3.1 Pro	Gemini 3 Pro	Sonnet 4.6	Opus 4.6	GPT-5.2
τ²-Bench (Retail)	90,8%	85,3%	91,7%	91,9%	82,0%
τ²-Bench (Telecom)	99,3%	98,0%	97,9%	99,3%	98,7%
MCP-Atlas	69,2%	54,1%	59,5%	59,5%	60,6%
APEX-Agents (Long Horizon)	33,5%	18,4%	—	29,8%	23,0%
MRCR v2 (8-needle)	84,9%	77,0%	84,9%	84,0%	83,8%
Sumber: (Google DeepMind, 2026)

Hasil komparasi ini mengungkapkan beberapa pola penting. Pertama, pada benchmark τ²-bench domain telecom, hampir semua model frontier mencapai performa yang tinggi (di atas 97%), mengindikasikan bahwa sistem percakapan dengan kontrol ganda (dual-control) mulai dapat ditangani dengan baik oleh model terkini. Kedua, pada benchmark MCP-Atlas yang menguji kemampuan penggunaan

Page 60
<page_number>50</page_number>

tool yang realistis, masih terdapat disparitas yang signifikan antar model (kisaran 54–69%), menunjukkan bahwa kemampuan multi-tool orchestration masih menjadi tantangan terbuka. Ketiga, pada APEX-Agents yang mengevaluasi tugas-tugas profesional jangka panjang, bahkan model terbaik (Gemini 3.1 Pro) hanya mencapai 33,5%, mengindikasikan masih terdapat kesenjangan yang signifikan antara kemampuan AI dan pelaksanaan pekerjaan profesional yang kompleks secara otonom.

Dalam konteks penelitian ini, benchmark-benchmark tersebut memberikan landasan untuk mengevaluasi performa sistem Agentic AI yang dibangun, khususnya kemampuan penggunaan MCP tool (τ²-Bench dan MCP-Atlas), kemampuan menangani workflow multi-langkah jangka panjang (APEX-Agents), dan kemampuan mempertahankan koherensi konteks selama proses data entry (MRCR v2). Pemilihan model LLM yang tepat dapat mempertimbangkan trade-off antara kemampuan agentic, latensi, dan biaya, menjadi keputusan arsitektural kritis yang harus diinformasikan oleh data benchmark tersebut.

2.16 Guardrails
Seiring dengan meningkatnya integrasi LLM dalam berbagai aplikasi sehari-hari, kebutuhan untuk mengidentifikasi dan memitigasi risiko yang ditimbulkannya menjadi semakin kritis, terutama ketika risiko tersebut dapat memberikan dampak mendalam bagi pengguna dan masyarakat luas. Sebagai respons terhadap tantangan ini, guardrails telah muncul sebagai teknologi pengamanan inti yang bertugas memfilter masukan atau keluaran dari LLM. Menurut (Dong dkk., 2024), guardrail didefinisikan sebagai suatu algoritma yang menerima sekumpulan objek sebagai masukan, seperti masukan dan/atau keluaran dari LLM, kemudian menentukan apakah dan bagaimana tindakan penegakan tertentu dapat diambil guna mengurangi risiko yang terkandung dalam objek-objek tersebut. Sebagai contoh, apabila masukan kepada LLM berkaitan dengan eksploitasi anak, guardrail dapat menghentikan masukan tersebut agar tidak diproses oleh LLM atau mengadaptasi keluarannya sehingga menjadi tidak berbahaya.

Page 61
<page_number>51</page_number>

Dalam konteks penelitian ini, guardrails diimplementasikan sebagai lapisan perlindungan pertama dalam arsitektur sistem sebelum permintaan pengguna diproses oleh supervisor agent. Lapisan guardrails terdiri dari dua komponen utama yang berjalan secara paralel, yaitu komponen deteksi prompt injection dan jailbreaking menggunakan model klasifikasi khusus, serta komponen blacklist domain menggunakan pendekatan LLM as judge untuk menyaring topik-topik yang berada di luar cakupan sistem.

2.16.1 Prompt Injection dan Jailbreaking

Kerentanan fundamental dari LLM yang terintegrasi dalam aplikasi terletak pada kesulitan model untuk membedakan antara instruksi sistem yang terpercaya dengan data yang diberikan oleh pengguna yang tidak terpercaya (Ivry dan Nahum, 2025). Kerentanan ini dieksploitasi melalui dua kategori serangan utama, yaitu prompt injection dan jailbreaking.

Y. Liu dkk., (2025) mendefinisikan prompt injection sebagai manipulasi keluaran model bahasa melalui prompt jahat yang direkayasa secara khusus. Arsitektur aplikasi berbasis LLM umumnya terdiri dari penyedia layanan yang membuat serangkaian prompt yang telah ditentukan sebelumnya dan dikombinasikan dengan masukan pengguna sebelum dikirimkan ke LLM. Serangan prompt injection terjadi ketika seorang adversari menyisipkan instruksi berbahaya ke dalam masukannya sehingga dapat mempengaruhi atau menganulir prompt yang telah ditentukan sebelumnya dalam versi gabungannya. Y. Liu dkk., (2025) mengidentifikasi dua kategori utama serangan prompt injection yaitu kategori pertama menargetkan aplikasi dengan konteks atau prompt yang diketahui, di mana pengguna jahat menyuntikkan prompt berbahaya ke dalam masukannya untuk memanipulasi aplikasi agar merespon query yang berbeda dari tujuan aslinya dan kategori kedua merupakan serangan yang lebih canggih di mana adversari berupaya mencemari aplikasi berbasis LLM melalui sumber-sumber internet seperti situs web atau email yang mengandung payload berbahaya.

Sementara itu, jailbreaking merupakan jenis serangan yang berbeda namun berkaitan erat. Shen dkk., (2024) mendefinisikan jailbreak prompts sebagai prompt

Page 62
<page_number>52</page_number>

yang dirancang secara sengaja untuk melewati perlindungan bawaan LLM, sehingga memunculkan konten berbahaya yang melanggar kebijakan penggunaan yang ditetapkan oleh vendor LLM. Tidak seperti prompt injection yang memanipulasi konteks atau instruksi sistem, jailbreaking secara langsung menargetkan kemampuan keamanan yang ditanamkan selama proses pelatihan model.

Fomin, (2026) menekankan bahwa deteksi serangan prompt injection dan jailbreaking menjadi sangat kritis untuk deployment sistem Agentic AI yang aman, terutama karena agen-agen tersebut semakin banyak memproses data yang tidak terpercaya dari berbagai sumber seperti email, dokumen, keluaran tool, dan API eksternal. Fomin, (2026) juga mengidentifikasi bahwa tantangan utama dalam evaluasi model deteksi terletak pada distribution shift antara data pelatihan dan data dunia nyata, di mana banyak model menunjukkan penurunan performa yang signifikan ketika dihadapkan pada pola serangan baru yang belum pernah dijumpai sebelumnya.

Dalam penelitian ini, deteksi prompt injection dan jailbreaking diimplementasikan menggunakan model Llama Prompt Guard 2 yang dikembangkan oleh Meta AI (Meta, 2024). Model ini dirancang untuk mendeteksi dua kategori serangan utama yaitu prompt injections yang memanipulasi data pihak ketiga dan pengguna yang tidak tepercaya dalam context window untuk membuat model mengeksekusi instruksi yang tidak diinginkan, serta jailbreaks yang merupakan instruksi jahat yang dirancang untuk mengesampingkan fitur keamanan yang telah dibangun ke dalam model.

2.16.2 Blacklist Domain dengan LLM as Judge

Selain perlindungan terhadap serangan teknis berupa prompt injection dan jailbreaking, sistem Agentic AI yang berinteraksi dengan pengguna secara luas juga memerlukan mekanisme untuk membatasi topik-topik yang tidak relevan atau berpotensi merugikan. Dalam konteks penelitian ini, dua domain yang masuk dalam kategori blacklist adalah konten bermuatan SARA (Suku, Agama, Ras, dan Antargolongan) serta saran keuangan atau investasi yang bersifat personal.

Page 63
<page_number>53</page_number>

Pendekatan yang digunakan untuk deteksi blacklist domain adalah LLM as judge, di mana sebuah LLM dimanfaatkan sebagai evaluator untuk menilai apakah masukan pengguna termasuk dalam domain yang dilarang. Gu dkk., (2025) mendefinisikan LLM as judge sebagai pendekatan di mana LLM digunakan sebagai evaluator untuk tugas-tugas yang kompleks, memanfaatkan kemampuan LLM untuk meniru penalaran seperti manusia sambil menawarkan solusi yang efektif dari segi biaya dan dapat diskalakan dengan mudah. Secara formal, proses evaluasi LLM as judge dapat dinyatakan sebagai berikut:

$$ \mathcal{E} \leftarrow \mathcal{P}_{LLM}(x \oplus C) \quad (2.13) $$

$\mathcal{E}$ adalah evaluasi akhir yang diperoleh dari seluruh proses LLM as judge dalam format yang diharapkan, yang dapat berupa skor, pilihan, label, atau kalimat.
$\mathcal{P}_{LLM}$ adalah fungsi probabilitas yang didefinisikan oleh LLM yang bersangkutan, di mana pembangkitan dilakukan melalui proses autoregresif.
x adalah data masukan dalam bentuk yang tersedia, dalam hal ini berupa teks permintaan pengguna yang akan dievaluasi.
C adalah konteks untuk masukan x, yang umumnya berupa template prompt yang mendefinisikan aturan dan kriteria evaluasi.
$\oplus$ adalah operator kombinasi yang menggabungkan masukan x dengan konteks C
Pendekatan berbasis LLM as judge ini dipilih karena kemampuannya untuk memahami nuansa semantik dalam masukan yang tidak selalu dapat ditangkap oleh pendekatan berbasis aturan statis. Implementasi blacklist domain dalam penelitian ini difokuskan pada dua area kritis, yaitu konten bermuatan SARA dan saran keuangan atau investasi personal. Penyaringan konten SARA (suku, agama, ras, dan antargolongan) dilakukan untuk memitigasi risiko konflik sosial, polarisasi, dan penyebaran misinformasi yang dapat diperkuat secara sistemis oleh algoritma AI sehingga mengancam stabilitas nilai sosial (Ompusunggu dan Sinambela, 2025; Samson Olufemi Olanipekun, 2025; Santoso dkk., 2025). Di sisi lain, pembatasan terhadap saran keuangan personal diterapkan karena adanya risiko knowledge conflict antara data statis model dengan dinamika pasar real-time, potensi halusinasi

Page 64
<page_number>54</page_number>

pada konsep finansial yang kompleks, hingga adanya bias kognitif inheren yang dapat memicu kerugian finansial nyata bagi pengguna (Kang dan Liu, 2023; Lee dkk., 2025; Winder, Hildebrand dan Hartmann, 2025). Selain itu, proteksi ini berfungsi sebagai langkah preventif terhadap serangan prompt injection yang berpotensi mengeksploitasi workflow keuangan untuk melanggar regulasi kepatuhan (Ishrak Alim, 2025). Gambar 2.11 contoh flow LLM-as-judge.

<img>Diagram showing the LLM-as-judge system overview. The diagram is divided into three main sections: Input, System, and Output. Input:

Evaluation Type: Pointwise, Pairwise, Listwise.
Evaluation Criteria: Fluency, Grammar, Relevance, Factuality, Informativeness, Completeness.
Evaluation References: Reference-Based, Reference-Free. System:
LLM-as-Judges Evaluation System: Single-LLM, Multiple-LLM, Human-AI.
A visual representation of data inputs (documents, images, audio) feeding into the evaluation system.
A visual representation of multiple LLMs collaborating with a human. Output:
Evaluation Results: Score (A+), Ranking (A+, A, B), Category (OO).
Explanation: Reasoning Steps, Justifications, Decision-making.
Feedback: Suggestions, Recommendations, Results, Improve.</img>
Gambar 2.11 Overview sistem LLM-as-judge (H. Li dkk., 2024)

2.17 Basis Data SQLite
SQLite merupakan sistem manajemen database relasional yang bersifat serverless, self-contained, dan dapat dijalankan tanpa proses server yang terpisah. Seluruh data database disimpan dalam satu file pada filesystem host, yang menjadikannya sangat sederhana dalam hal deployment dan tidak memerlukan konfigurasi server database yang kompleks. Sebagai mesin basis data yang paling banyak di-deploy di dunia, SQLite digunakan oleh berbagai peramban web terkemuka, sistem operasi, ponsel, dan sistem tertanam lainnya (SQLite, 2026).

Dalam konteks sistem penelitian ini, SQLite berperan sebagai single source of truth yang menyimpan seluruh data persisten sistem, mencakup riwayat

Page 65
<page_number>55</page_number>

percakapan, serta hasil ekstraksi OCR dalam format JSON. Pilihan SQLite didasarkan pada beberapa pertimbangan teknis, yaitu kesederhanaan deployment dalam lingkungan pengembangan, performa baca-tulis yang memadai untuk skala penggunaan penelitian ini, dukungan native Python melalui modul sqlite3 standar, serta kompatibilitas dengan library aiosqlite untuk operasi database asinkron yang dibutuhkan dalam arsitektur FastAPI berbasis asyncio (FastAPI, 2026).

Erike dkk., (2025) melalui evaluasi performa komparatif antara SQLite, MySQL, dan Firebase menggunakan pendekatan parallel execution menemukan bahwa SQLite mencapai waktu rata-rata tercepat pada operasi baca sebesar 10,8 ms untuk data teks, mengungguli kedua kompetitornya. Keunggulan performa baca tersebut menjadi fondasi krusial bagi implementasi sistem memori yang dinamis pada LLM agent.

Penggunaan SQLite dalam penelitian ini selaras dengan konsep A-MEM (Agentic Memory) yang diusulkan oleh W. Xu dkk., (2025), di mana agen memerlukan sistem memori yang tidak hanya berfungsi sebagai penyimpanan statis, tetapi mampu mengorganisasikan pengalaman historis secara mandiri melalui pengindeksan dan keterhubungan antar data. Prinsip single writer diterapkan pada SQLite untuk menghindari race condition pada operasi tulis, di mana seluruh penulisan ke database dari sisi agent dilakukan secara eksklusif melalui MCP-SQLite sebagai satu-satunya titik akses yang dikontrol untuk operasi tulis dari layer agent.

2.18 Google Sheets
Google Sheets adalah platform spreadsheet berbasis cloud yang dikembangkan oleh Google dan dapat diakses melalui peramban web maupun aplikasi mobile tanpa memerlukan instalasi perangkat lunak tambahan. Platform ini menyediakan Google Sheets API sebagai antarmuka pemrograman yang memungkinkan aplikasi eksternal melakukan operasi baca (read) dan tulis (write) terhadap data spreadsheet secara programatik melalui protokol HTTP yang terstandarkan (De Matos dkk., 2025).

Page 66
<page_number>56</page_number>

Dalam konteks sistem agentic yang membutuhkan output data yang dapat diakses dan dikelola oleh pengguna bisnis secara langsung, Google Sheets menjadi pilihan yang tepat sebagai repositori hasil data entry. Kemampuan kolaborasi real-time Google Sheets memungkinkan beberapa pengguna mengakses dan memantau data yang sama secara bersamaan, yang relevan dalam skenario di mana hasil ekstraksi struk perlu ditinjau atau diteruskan ke pihak lain dalam tim. Selain itu, antarmuka spreadsheet yang familiar bagi pengguna bisnis umum menjadikan Google Sheets sebagai format output yang tidak memerlukan kurva pembelajaran (learning curve) tambahan dari sisi pengguna akhir (end-user).

Integrasi Google Sheets dalam arsitektur sistem penelitian ini dilakukan melalui MCP-GSheets yang mengekspos Google Sheets API sebagai kumpulan tool yang dapat dipanggil oleh agent. Pendekatan ini memisahkan logika pengambilan keputusan agent dari implementasi teknis komunikasi dengan API Google, sehingga operasi seperti pembuatan sheet baru, pembaruan sel (cell), dan penambahan baris data dapat dilakukan oleh Data Entry Team Agent melalui tool yang terdefinisi dengan kontrak yang eksplisit. Pemilihan Google Sheets sebagai medium output data entry juga mempertimbangkan kemampuannya untuk berfungsi sebagai lapisan visualisasi data yang dapat langsung diolah lebih lanjut oleh pengguna, seperti pembuatan grafik, penerapan formula, atau ekspor ke format lain, tanpa ketergantungan pada sistem tambahan.

2.19 Evaluation Metrics

Evaluasi performa sistem Agentic AI untuk otomatisasi data entry memerlukan metrik yang mampu mengukur berbagai aspek kualitas secara komprehensif. Sistem yang dibangun dalam penelitian ini melibatkan dua tahapan utama yang masing-masing membutuhkan metrik evaluasi yang berbeda, yaitu tahapan ekstraksi informasi dari dokumen struk pembelian dan tahapan pemanggilan tool MCP oleh agent. Berdasarkan hal tersebut, penelitian ini menggunakan tiga kelompok metrik evaluasi yang saling melengkapi. Kelompok pertama adalah KIEval, yang mengukur kualitas ekstraksi informasi kunci dari dokumen dengan mempertimbangkan relasi struktural antar entitas. Kelompok

Page 67
<page_number>57</page_number>

kedua adalah ANLS*, yang mengevaluasi kemiripan antara output generatif model dengan ground truth menggunakan pendekatan berbasis jarak edit yang dinormalisasi dan mampu menangani struktur data yang kompleks. Kelompok ketiga adalah MCP tool accuracy, yang mengukur keakuratan pemanggilan tool oleh agent melalui dua sub-metrik, yaitu AST accuracy dan Pass@K accuracy.

2.19.1 Key Information Extraction Evaluation (KIEval)

Key Information Extraction Evaluation (KIEval) merupakan metrik evaluasi yang dirancang khusus untuk menilai performa model dokumen KIE dengan perspektif yang berorientasi pada kebutuhan aplikasi industri. Berbeda dari metrik konvensional seperti entity-level F1 score yang hanya menilai ekstraksi entitas secara individual tanpa mempertimbangkan relasi struktural antar entitas, KIEval diformulasikan untuk mengevaluasi model KIE pada dua tingkatan sekaligus, yaitu tingkat entitas (entity-level) dan tingkat grup (group-level). Motivasi pengembangan KIEval berakar pada dua permasalahan mendasar yang ditemukan pada metrik-metrik yang ada sebelumnya. Pertama, metrik yang ada mengabaikan sifat terstruktur dari informasi dalam dokumen, di mana pasangan kunci-nilai yang diekstraksi seringkali memiliki keterkaitan kontekstual satu sama lain, seperti pada data set CORD (Consolidated Receipt Dataset) relasi antara Menu.name, Menu.quantity, dan Menu.price pada dokumen struk pembelian. Kedua, formulasi metrik yang ada tidak selaras dengan kebutuhan aplikasi industri nyata, di mana kesalahan KIE lebih relevan diukur dalam satuan jumlah langkah koreksi yang diperlukan daripada pemisahan antara false positive (FP) dan false negative (FN) yang lazim digunakan pada metrik berbasis model (Khang dkk., 2025).

Inti dari KIEval adalah mekanisme group-matching yang dilakukan sebelum evaluasi pada tingkat entitas maupun grup. Misalkan PR = {pr₁, pr₂, ..., prₙ} adalah himpunan grup yang diprediksi dan GT = {gt₁, gt₂, ..., gtₘ} adalah himpunan grup ground truth, di mana setiap grup terdiri dari sekumpulan entitas yang direpresentasikan sebagai pasangan (entity-type, value). Skor pencocokan S(n, m) didefinisikan sebagai jumlah entitas identik antara prₙ dan

Page 68
<page_number>58</page_number>

gtm. Berdasarkan skor pencocokan tersebut, setiap grup prediksi dicocokkan dengan satu grup ground truth menggunakan Hungarian matching algorithm untuk menghasilkan himpunan grup yang telah dicocokkan: G = Hungarian(PR, GT, S) (2.14) di mana S menyatakan himpunan skor pencocokan S(n,m) antara seluruh pasangan prediksi dan ground truth. Untuk sebuah entitas e pada pasangan pencocokan (n, m), statistik TP, FN, dan FP kemudian dihitung sebagai berikut: TPe(n,m) = Se(n,m), FNe(n,m) = Ne(gtm) - Se(n,m), FPe(n,m) = Ne(prn) - Se(n,m) (2.15) di mana Se(n,m) menyatakan jumlah pasangan entitas identik bertipe e antara grup prediksi ke-n dan grup ground truth ke-m, sedangkan Ne(·) menyatakan operasi penghitungan entitas bertipe e dalam suatu grup. Berdasarkan statistik tersebut, KIEval Entity F1 dihitung dengan mengakumulasi seluruh statistik TP, FN, dan FP dari seluruh pasangan dalam G sebagai berikut: TPentity = Σ(n,m)∈G Σe TPe(n,m) (2.16) FNentity = Σm=1M Σe Ne(gtm) - TPentity (2.17) FPentity = Σn=1N Σe Ne(prn) - TPentity (2.18)

Statistik-statistik tersebut kemudian digunakan untuk menghitung KIEval Entity F1 menggunakan formulasi presisi dan recall standar. Dalam konteks penelitian ini, KIEval diterapkan untuk mengukur kualitas ekstraksi informasi kunci dari struk pembelian yang dihasilkan oleh extraction agent berbasis GLM-OCR. Metrik KIEval Entity F1 mengukur sejauh mana entitas-entitas individual seperti nama toko, tanggal transaksi, nama item, dan harga diekstraksi dengan benar.

Page 69
<page_number>59</page_number>

2.19.2 Average Normalized Levenshtein Similarity Star (ANLS)*

Average Normalized Levenshtein Similarity star (ANLS*) merupakan metrik evaluasi universal yang dirancang untuk menilai performa model generatif pada berbagai tugas pemrosesan dokumen, termasuk ekstraksi informasi dan klasifikasi. Metrik ini diperkenalkan oleh Peer dkk., 2025 sebagai pengembangan dan pengganti langsung dari metrik ANLS yang telah ada sebelumnya, dengan kemampuan yang diperluas untuk menangani tipe data yang lebih beragam, meliputi string, None, Tuple, List, Dictionary, serta berbagai kombinasi rekursifnya. Motivasi pengembangan ANLS* berasal dari keterbatasan pada metrik-metrik sebelumnya seperti berbasis exact match F1 score tidak sesuai untuk model generatif karena output yang dihasilkan berupa teks bebas yang mungkin mengandung variasi kecil namun secara semantik masih benar. Metrik ini memberikan evaluasi yang lebih representatif terhadap performa model generatif dalam mengekstraksi dan merepresentasikan informasi terstruktur dari dokumen. Secara formal, ANLS* didefinisikan sebagai:

ANLS* (g, p) = $\frac{s(g, p)}{l(g, p)}$ (2.19)

di mana g adalah ground truth, p adalah prediksi, sehingga ANLS* (g, p) $\in$ [0,1] . Setiap prediksi dalam pohon tersebut diberikan bobot yang setara, sehingga simpul daun (leaf nodes) pada sub-pohon besar memiliki bobot yang sama dengan simpul daun yang muncul di tingkat atas.

Fungsi skor s didefinisikan secara rekursif untuk mengukur kemiripan antara ground truth dan prediksi, disesuaikan dengan tipe data masing-masing:

s(g, p) = $\begin{cases} 1.0 & \text{if } g = p \ 1.0 - \frac{LD(g, p)}{\max(|g|, |p|)} & \text{if } g \neq p \text{ and } g, p \text{ are strings} \ s(g_i, p) \text{ with } i = \arg\max_i \left( \text{ANLS}^*(g_i, p) \right) & \text{if } g \text{ is a list and } p \text{ is a list} \ \sum_{(g_i, p_i) \in \psi(g, p)} s(g_i, p_i) & \text{if } g \text{ is a dictionary and } p \text{ is a dictionary} \ \sum_{k \in \text{keys}(p)} s(g_k, p_k) & \text{if } g \text{ is a dictionary and } p \text{ is a dictionary} \ 0.0 & \text{otherwise} \end{cases}$ (2.20)

Page 70
<page_number>60</page_number>

if type(g) = type(p) = None if type(g) = type(p) = String and s(g, p) ≥ τ if type(g) = Tuple if type(g) = type(p) = List if type(g) = type(p) = Dict and k ∈ keys(p) otherwise

di mana LD adalah jarak Levenshtein, τ = 0,5 adalah ambang batas normalized Levenshtein distance yang apabila dilampaui maka skor dianggap 0, dan ψ adalah algoritma Hungarian matching yang dieksekusi berdasarkan skor ANLS* berpasangan antara setiap elemen ground truth dan prediksi. Ketidakcocokan tipe (type mismatch) menghasilkan skor 0.0.

Untuk menormalisasi skor s, fungsi panjang l didefinisikan secara rekursif pada rumus 2.28 sebagai berikut:

l(g, p) = $$ \begin{cases} 1 & \text{if } \text{type}(x) = \text{type}(p) = \text{None} \ 1 & \text{if } \text{type}(g) = \text{type}(p) = \text{String} \ 1 & \text{if } \text{type}(g) = \text{Tuple} \ l(g_i, p) \text{ with } i = \arg\max 2_i \left( \text{ANLS}^*(g_i, p) \right) \ \quad + \sum_{(g_i, p_i) \in \psi(g, p)} l(g_i, p_i) \ \quad + \sum_{g_u \notin \psi(g, p)} l_t(g_u) \ \quad + \sum_{p_u \notin \psi(g, p)} l_t(p_u) \ \quad + \sum_{k \in \text{keys}(p) \cap \text{keys}(g)} l(g_k, p_k) \ \quad + \sum_{k \in \text{keys}(g) - \text{keys}(p)} l_t(g_k) \ \quad + \sum_{k \in \text{keys}(p) - \text{keys}(g)} l_t(p_k) \ \quad + \max(l_t(g), l_t(p)) & \text{if } \text{type}(g) = \text{Tuple} \end{cases} \quad (2.21) $$

Page 71
<page_number>61</page_number>

if type(g) = type(p) = List if type(g) = type(p) = Dict otherwise

Ketidakcocokan tipe pada sub-pohon ditangani melalui fungsi panjang $l_t$ yang didefinisikan sebagai berikut:

$$ l_t(x) = \begin{cases} 1 & \text{if type(x) = None} \ 1 & \text{if type(x) = String} \ \max_{x_i \in x} l_t(x_i) & \text{if type(x) = Tuple} \ \sum_{x_i \in x} l_t(x_i) & \text{if type(x) = List} \ \sum_{k \in \text{keys}(x)} l_t(x_k) & \text{if type(x) = Dict} \end{cases} \quad (2.22) $$

di mana x adalah sub-pohon dari prediksi p maupun sub-pohon dari ground truth g. Penggunaan $\max(l_t(g), l_t(p))$ pada kasus ketidakcocokan tipe memastikan bahwa baik sub-pohon yang hilang maupun sub-pohon yang dihalusinasi mendapatkan penalti yang setara.

Keunggulan ANLS* dibandingkan metrik-metrik sebelumnya terletak pada kemampuannya menangani berbagai tipe data secara rekursif dalam satu kerangka yang terpadu. Pada tipe String, digunakan normalized levenshtein similarity dengan ambang batas $\tau = 0,5$, sehingga prediksi dengan jarak edit melebihi setengah panjang string dianggap salah total. Pada tipe List, algoritma Hungarian matching digunakan untuk menemukan pasangan optimal antara elemen-elemen prediksi dan ground truth tanpa memperhatikan urutan, sehingga elemen yang hilang maupun yang dihalusinasi mendapat penalti. Pada tipe Dict, pencocokan dilakukan berdasarkan kunci, sehingga kunci yang hilang maupun yang dihalusinasi mendapat penalti secara simetris.

2.19.3 Digit Accuracy

KIEVal dan ANLS* belum cukup untuk mengevaluasi keakuratan numerik pada field harga. ANLS* menggunakan jarak Levenshtein yang ternormalisasi pada level karakter, sehingga prediksi “2000” terhadap ground truth “9000”

Page 72
<page_number>62</page_number>

menghasilkan skor yang tinggi karena hanya berbeda satu karakter dari empat karakter total (NLS = 1/4 = 0,25, skor = 0,75), padahal selisih nilai moneter sesungguhnya adalah Rp 7.000. Ketidaksesuaian ini mendorong diusulkannya metrik digit accuracy sebagai metrik komplementer yang bersifat exact-match pada representasi digit dari field-field harga.

Misalkan $\mathcal{F}$ adalah himpunan seluruh field harga yang dievaluasi. Untuk setiap field $f \in \mathcal{F}$ pada sampel ke-$i$, didefinisikan fungsi normalisasi digit sebagai berikut. $$ d(v) = \text{concat}({c \mid c \in v, c \in {0,1,...,9}}) \quad 2.23 $$ di mana $v$ adalah nilai string dari suatu field dan $d(v)$ adalah hasil konkatenasi seluruh karakter digit yang terkandung di dalamnya, dengan mengabaikan titik desimal, koma, simbol mata uang, dan spasi. Dengan demikian, representasi seperti "Rp 12.500", "12,500", dan "12500" semuanya menghasilkan $d(v) = "12500"$.

Untuk setiap pasangan field prediksi $\widehat{v_{f,i}}$ dan ground truth $v_{f,i}^$, indikator kecocokan digit didefinisikan sebagai berikut. $$ \mathbb{1}{digit}(f,i) = \begin{cases} 1 & \text{if } d(\widehat{v{f,i}}) = d(v_{f,i}^) \text{ dan } d(v_{f,i}^) \neq \emptyset \ 0 & \text{if } d(\widehat{v_{f,i}}) \neq d(v_{f,i}^) \text{ dan } d(v_{f,i}^*) \neq \emptyset \end{cases} \quad 2.24 $$

Field dengan $d(v_{f,i}^) = $, yaitu field harga yang memang tidak terisi pada ground truth, dikecualikan dari perhitungan agar tidak menggelembungkan denominasi. Digit Accuracy pada dataset dengan $N$ sampel diformulasikan sebagai berikut. $$ DA = \frac{\sum_{i=1}^{N} \sum_{f \in \mathcal{F}} \mathbb{1}{digit}(f,i)}{\sum{i=1}^{N} \sum_{f \in \mathcal{F}} \mathbb{1}[d(v_{f,i}^) \neq \emptyset]} \times 100% \quad 2.25 $$ di mana $\mathbb{1}[\cdot]$ adalah fungsi indikator biner, $N$ adalah jumlah sampel struk yang dievaluasi, dan $\mathcal{F}$ adalah himpunan field harga.

2.19.4 MCP Tool Accuracy

Evaluasi akurasi penggunaan tool MCP oleh agent memerlukan metrik yang mampu mengukur dua aspek yang berbeda namun saling melengkapi. Aspek

Page 73
<page_number>63</page_number>

pertama adalah kebenaran setiap pemanggilan tool secara individual, yang diukur menggunakan metrik AST accuracy. Aspek kedua adalah kebenaran output akhir dari keseluruhan workflow, yang diukur menggunakan metrik Pass@K. Kombinasi kedua metrik ini memberikan gambaran komprehensif tentang kemampuan agent dalam memilih tool yang tepat, mengisi parameter dengan benar, dan menghasilkan output yang sesuai dengan ekspektasi. Fan dkk., (2025) dalam benchmark MCPToolBench++ menunjukkan bahwa peringkat AST accuracy dan Pass@K tidak selalu berkorelasi positif, sehingga kedua metrik tersebut diperlukan secara bersamaan untuk diagnosis performa yang lebih lengkap.

Abstract Syntax Tree (AST)
Abstract Syntax Tree (AST) merupakan metrik yang mengukur kebenaran setiap pemanggilan tool oleh agent dengan cara membandingkan output yang dihasilkan terhadap label ground truth menggunakan pendekatan pohon sintaksis abstrak. Pendekatan ini pertama kali diperkenalkan secara sistematis oleh Patil dkk., 2025 pada Berkeley Function Calling Leaderboard (BFCL) dan kemudian diadopsi secara luas untuk evaluasi MCP tool use. Evaluasi AST bersifat all-or-nothing atau exact match, di mana sebuah pemanggilan tool hanya dianggap benar jika seluruh komponennya tepat secara bersamaan tanpa toleransi terhadap kesalahan parsial.

Tiga komponen yang dievaluasi dalam AST Accuracy adalah sebagai berikut. Pertama, kecocokan nama fungsi (function match), yang memverifikasi bahwa nama tool yang dipanggil oleh agent sesuai dengan ground truth. Kedua, kecocokan parameter wajib (required parameter match), yang memastikan seluruh parameter yang diwajibkan oleh skema tool tersedia dalam panggilan dan tidak ada parameter yang tidak dikenal dari skema yang digunakan. Ketiga, kecocokan tipe dan nilai parameter (parameter type and value match), yang memverifikasi bahwa tipe data dan nilai dari setiap parameter sesuai dengan ekspektasi ground truth secara tepat. Skor AST untuk satu pemanggilan tool ke-i didefinisikan menggunakan logika konjungsi (AND), di mana pemanggilan tool hanya dianggap benar jika seluruh komponen tersebut terpenuhi:

$$ \text{AST}_i = 1 \left[ (\widehat{f}_i = f_i) \land (\widehat{p_i^{\text{req}}} = p_i^{\text{req}}) \land (\widehat{p_i^{\text{val}}} = p_i^{\text{val}}) \right] \quad (2.26) $$

Page 74
<page_number>64</page_number>

di mana fi adalah nama fungsi ground truth, f̂i adalah nama fungsi yang diprediksi oleh agent, pireq adalah himpunan parameter wajib ground truth, p̂ireq adalah himpunan parameter wajib yang diprediksi, pival adalah himpunan tipe dan nilai parameter ground truth, p̂ival adalah himpunan tipe dan nilai parameter yang diprediksi, dan 1[•] adalah fungsi indikator yang bernilai 1 jika seluruh kondisi terpenuhi dan bernilai 0 jika terdapat satu kondisi saja yang tidak sesuai.

AST accuracy untuk satu test case yang melibatkan M pemanggilan tool adalah rata-rata skor seluruh pemanggilan tool dalam test case tersebut:

AST_Accuracyj = $\frac{1}{M} \sum_{i=1}^{M} \text{AST}_i$ (2.27)

Untuk keseluruhan dataset yang terdiri dari N test case, AST accuracy dihitung sebagai rata-rata dari seluruh test case:

$\overline{\text{AST_Accuracy}} = \frac{1}{N} \sum_{j=1}^{N} \text{AST_Accuracy}_j$ (2.28)

Pass@K
Pass@K merupakan metrik yang mengukur peluang agent menghasilkan output akhir yang benar setidaknya dalam satu dari K percobaan independen. Metrik ini pertama kali diperkenalkan oleh Chen dkk., (2021) dalam konteks evaluasi model code generation pada benchmark HumanEval untuk mengatasi keterbatasan metrik exact match sederhana dalam mengakomodasi variabilitas stokastik output model generatif. Kemampuan pass@k untuk mengukur fungsional kebenaran, yaitu apakah output memenuhi kriteria kebenaran yang ditetapkan daripada hanya mencocokkan string secara harfiah, menjadikannya metrik yang lebih representatif untuk mengevaluasi sistem agentic yang menghasilkan output berupa tindakan nyata seperti penulisan data ke spreadsheet.

Secara formal, untuk mengevaluasi Pass@K, sebanyak n ≥ k sampel dihasilkan per test case, kemudian dihitung jumlah sampel yang benar c ≤ n yang memenuhi kriteria kebenaran yang ditetapkan. Estimator unbiased dari Pass@K yang menghindari varians tinggi dari estimasi naif didefinisikan sebagai berikut:

Page 75
<page_number>65</page_number>

$$ pass@k = 1 - \frac{\binom{n-c}{k}}{\binom{n}{k}} \quad (2.29) $$

di mana n adalah total sampel yang dihasilkan per test case, c adalah jumlah sampel yang benar, dan k adalah jumlah sampel yang dipilih untuk evaluasi.

Untuk sistem data entry pada penelitian ini, Pass@K digunakan dalam konfigurasi K = 1 (Pass@1) dengan n = 1 sampel per test case, karena sistem produksi mensyaratkan kebenaran pada percobaan pertama tanpa mekanisme retry. Dalam kondisi khusus ini, estimator menyederhanakan menjadi ekspektasi keberhasilan empiris, dan indikator keberhasilan untuk satu test case j didefinisikan sebagai:

$$ Pass@1_j = c_{j,1} = \begin{cases} 1 & \text{Jika output akhir agent } \equiv \text{ ground truth} \ 0 & \text{Jika sebaliknya} \end{cases} \quad (2.30) $$

di mana $c_{j,1} \in {0,1}$ adalah indikator keberhasilan percobaan ke-1 pada test case j, yang bernilai 1 jika output akhir agent sesuai dengan ground truth dan bernilai 0 jika tidak. Pass@1 keseluruhan untuk dataset dengan N test case kemudian dihitung sebagai:

$$ \overline{Pass@1} = \frac{1}{N} \sum_{j=1}^{N} Pass@1_j \quad (2.31) $$

Dalam konteks penelitian ini, Pass@1 mengukur apakah keseluruhan workflow agent, mulai dari pembacaan dokumen oleh extraction agent, pengambilan keputusan oleh supervisor agent, hingga penulisan data ke Google Sheets oleh Data Entry Team melalui MCP, menghasilkan output akhir yang benar pada percobaan pertama. Sebuah test case dianggap berhasil (Pass@1 = 1) apabila seluruh data yang tertulis ke dalam spreadsheet sesuai dengan ground truth yang telah dianotasi secara manual, mencakup kebenaran nilai entitas, kelengkapan struktur, dan keakuratan penempatan data pada baris dan kolom yang tepat.

Kombinasi antara AST dan Pass@1 saling melengkapi dalam mengevaluasi performa sistem secara menyeluruh. AST mengukur process quality agent dalam mengeksekusi MCP tools, mencakup kebenaran nama fungsi, parameter wajib,

Page 76
<page_number>66</page_number>

serta nilai parameter yang dipanggil pada setiap langkah eksekusi. Sementara itu, Pass@1 mengukur outcome quality yang dihasilkan sistem, yaitu apakah data struk yang diekstraksi berhasil ditulis secara benar ke Google Sheets dalam satu kali percobaan tanpa retry.

2.20 React Native dan Expo
React Native adalah framework pengembangan aplikasi mobile lintas platform (cross-platform) yang dikembangkan oleh Meta dan pertama kali dirilis secara publik pada tahun 2015 (Hutri, 2023). Framework ini memungkinkan pengembang membangun aplikasi native untuk Android dan iOS menggunakan satu basis kode tunggal (single codebase) yang ditulis dalam JavaScript dengan komponen React, sehingga secara signifikan mengurangi duplikasi effort pengembangan dibandingkan dengan pendekatan native yang memerlukan basis kode terpisah untuk setiap platform (Ali dan Shubham, 2020). React Native mengompilasi komponen JavaScript ke komponen UI native platform yang sesungguhnya, bukan ke dalam WebView, sehingga menghasilkan performa dan tampilan yang tidak berbeda dari aplikasi yang dibangun menggunakan bahasa native platform secara langsung.

Expo adalah toolchain dan managed runtime yang dibangun di atas React Native, menyediakan lapisan abstraksi yang menyederhanakan proses pengembangan, build, dan distribusi aplikasi. Expo menawarkan platform-neutral API yang mengizinkan pengembang mengakses fitur perangkat native seperti kamera dan notifikasi tanpa perlu menulis kode yang berspesifik pada platform tertentu. Keunggulan Expo dibandingkan penggunaan React Native secara langsung meliputi kemudahan konfigurasi proyek, lingkungan build yang terkelola (managed), serta dukungan bawaan untuk deployment ke Android, iOS, dan web dari satu proyek yang sama.

2.21 Agile Scrum
Secara umum, metode pengembangan perangkat lunak dapat diklasifikasikan menjadi dua paradigma utama. Paradigma pertama adalah pendekatan plan-driven yang mencakup metode sekuensial

Page 77
<page_number>67</page_number>

seperti Waterfall serta metode iteratif formal seperti Rational Unified Process (RUP). Pendekatan ini sangat mengandalkan perencanaan matang dan dokumentasi lengkap di awal. Paradigma kedua adalah pendekatan agile, seperti Scrum, yang bersifat empiris dan adaptif. Berdasarkan penelitian Shafiee dkk., 2020, transisi dari RUP ke Scrum terbukti memberikan dampak positif dalam menghadapi fleksibilitas pengembangan sistem yang kompleks, yang mana sangat relevan dengan karakteristik pengembangan Agentic AI berbasis model generatif dengan komponen fine-tuning, integrasi MCP, dan evaluasi model yang memerlukan penyesuaian berkelanjutan berdasarkan hasil eksperimen, sehingga pendekatan Agile Scrum lebih sesuai untuk konteks ini.

Agile merupakan metodologi pengembangan perangkat lunak yang menekankan nilai-nilai adaptabilitas, kolaborasi, dan pengiriman perangkat lunak yang berfungsi secara inkremental (Itzik, D., dan Roy, G., 2023). Manifesto Agile yang dipublikasikan pada tahun 2001 menetapkan empat nilai utama yaitu individu dan interaksi lebih diutamakan daripada proses dan alat, perangkat lunak yang berfungsi lebih diutamakan daripada dokumentasi yang komprehensif, kolaborasi dengan pelanggan lebih diutamakan daripada negosiasi kontrak, dan respons terhadap perubahan lebih diutamakan daripada mengikuti rencana yang telah ditetapkan. Prinsip-prinsip ini relevan dalam pengembangan sistem AI modern, di mana integrasi AI ke dalam metodologi Agile terbukti meningkatkan efisiensi pengembangan, akurasi, dan keamanan sistem sekaligus mengurangi waktu pengembangan (Suranto dkk, 2023).

Scrum adalah salah satu implementasi Agile yang paling banyak digunakan, mengadopsi pendekatan empiris yang menerapkan konsep kontrol proses industri ke dalam pengembangan sistem. Scrum membagi proses pengembangan ke dalam tiga fase utama.

Fase Pre-Game mencakup perencanaan keseluruhan proyek dan penyusunan Product Backlog, yaitu daftar kebutuhan sistem yang diprioritaskan dan diperbarui secara berkelanjutan selama proses pengembangan.
Page 78
<page_number>68</page_number>

Fase Development (Game) merupakan inti dari Scrum yang terdiri dari serangkaian Sprint, yaitu siklus iteratif berdurasi satu hingga empat minggu di mana tim mengembangkan increment sistem yang dapat berfungsi.
Fase Post-Game mencakup integrasi akhir, pengujian sistem secara menyeluruh, dan persiapan rilis. Penerapan Agile Scrum dalam penelitian ini relevan mengingat temuan Suranto, 2023 yang menunjukkan bahwa integrasi AI dalam proses Agile dapat membantu mengidentifikasi dependensi dan konflik kebutuhan, memprioritaskan backlog, serta mengotomatisasi tugas-tugas pengembangan yang berulang.
2.22 Flowchart
Flowchart didefinisikan sebagai suatu diagram yang merepresentasikan secara visual urutan langkah-langkah yang terlibat dalam suatu proses atau sistem. Setiap langkah digambarkan menggunakan simbol tertentu, sedangkan panah digunakan untuk menunjukkan alur kendali atau aliran data antar langkah tersebut. Flowchart dimanfaatkan untuk memodelkan sistem atau proses sehingga memudahkan pengguna dalam memahami struktur serta urutan kejadian yang terjadi di dalamnya (Ghritlahare, 2025).

Tabel 2.5 Simbol - simbol flowchart diagram

Simbol	Nama	Keterangan
<img>Rectangle</img>	Proses	Sebuah proses yang dijalankan oleh komputer umumnya menghasilkan perubahan pada data atau informasi yang diproses.
<img>Parallelogram</img>	Input atau Output	Untuk menunjukkan proses masukan atau keluaran data dalam alur sistem.
<img>Diamond</img>	Decision (Logika)	Untuk menyatakan suatu kondisi dengan dua kemungkinan hasil, yaitu YA atau TIDAK.
Page 79
<page_number>69</page_number>

Tabel 2.5 Simbol - simbol flowchart diagram (Lanjutan)

Simbol	Nama	Keterangan
<img>Predefined Process symbol</img>	Predefined Process	Untuk menunjukkan penyediaan ruang penyimpanan dalam pemrosesan data agar menetapkan nilai awal.
<img>Terminal symbol</img>	Terminal	Untuk menunjukkan titik awal atau akhir dari suatu program.
2.23 Unified Modeling Language (UML) Unified Modeling Language atau UML digunakan dalam pengembangan sistem pada bidang rekayasa perangkat lunak sebagai bahasa visual untuk mendefinisikan dan mendokumentasikan suatu sistem. Melalui UML, kebutuhan sistem yang digambarkan dalam bentuk skenario penggunaan oleh pengguna dapat direpresentasikan secara jelas. Selain itu, berbagai batasan yang terdapat dalam sistem juga dapat dimodelkan menggunakan UML. Oleh karena itu, banyak peneliti yang bergerak di bidang rekayasa perangkat lunak mempublikasikan kajian mengenai pemanfaatan diagram UML dalam pengembangan sistem serta kontribusinya terhadap praktik rekayasa perangkat lunak guna mendukung perkembangan disiplin ilmu tersebut (Koç dkk., 2021).

Use Case Diagram Use case diagram merupakan diagram dalam UML yang digunakan untuk menggambarkan hubungan antara aktor dan fungsi-fungsi yang disediakan oleh sistem secara visual. Diagram ini menampilkan aktor sebagai pihak yang berinteraksi dengan sistem serta use case sebagai representasi layanan atau proses yang dapat dijalankan untuk mencapai tujuan tertentu. Use case diagram berfungsi memberikan gambaran umum mengenai ruang lingkup sistem, batasan sistem, serta interaksi yang terjadi antara pengguna dan sistem tanpa menjelaskan detail alur langkah di dalamnya. Dengan penyajian yang sederhana dan mudah dipahami, use
Page 80
<page_number>70</page_number>

case diagram membantu pemangku kepentingan dalam memahami kebutuhan fungsional sistem serta menjadi dasar dalam proses analisis dan perancangan sistem perangkat lunak (Vranić dkk., 2024).

Tabel 2.6 Simbol – simbol use case diagram

Gambar	Nama	Keterangan
<img>A stick figure representing an actor</img>	Aktor	Ketika aktor berkomunikasi dengan use case, mereka dapat berupa individu, sistem lain, atau alat.
<img>A dashed arrow pointing to the right</img>	Ketergantungan (dependency)	Hubungan di mana elemen yang tidak bersifat mandiri bergantung pada elemen yang berdiri sendiri jika diubah.
<img>A solid arrow pointing to the left</img>	Generalisasi	Menunjukkan bahwa seorang aktor memiliki kemampuan khusus yang memungkinkannya berpartisipasi dalam suatu kasus.
<img>A dashed arrow pointing to the right</img>	Include	Ini menunjukkan bahwa suatu kebutuhan sepenuhnya terintegrasi dalam fungsionalitas kebutuhan lain yang terkait.
<img>A solid arrow pointing to the left</img>	Extend	Menunjukkan bahwa sebuah use case menjadi perluasan fungsional dari use case lain ketika sebuah kondisi tertentu terpenuhi.
<img>A solid horizontal line</img>	Asosiasi	Pemetaan umum hubungan antara aktor dan kasus.
<img>A square representing a system</img>	Sistem	Menspesifikasikan paket yang menunjukkan sistem yang memiliki batasan tertentu.
<img>An oval representing a use case</img>	Kasus (use case)	Fungsionalitas yang ditawarkan oleh sistem dalam bentuk unit-unit yang dapat berinteraksi satu sama lain dengan bertukar pesan antar aktor atau unit.
Page 81
<page_number>71</page_number>

Activity Diagram
Activity diagram merupakan salah satu diagram dalam UML yang digunakan untuk menggambarkan perilaku sistem dalam bentuk alur kendali dari satu aktivitas ke aktivitas lainnya. Diagram ini merepresentasikan rangkaian tindakan yang dilakukan secara terkoordinasi oleh sistem untuk mencapai suatu tujuan tertentu. Alur aktivitas dimulai dari titik awal dan berakhir pada titik akhir, dengan setiap aktivitas digambarkan sebagai langkah kerja yang saling terhubung melalui panah sebagai penunjuk aliran proses. Activity diagram juga mendukung percabangan, penggabungan, serta proses paralel untuk memodelkan berbagai kemungkinan alur yang dapat terjadi dalam sistem. Selain itu, diagram ini dapat dibagi ke dalam swimlane untuk menunjukkan pihak atau aktor yang bertanggung jawab terhadap setiap aktivitas. Dengan demikian, activity diagram membantu dalam memahami proses bisnis atau logika sistem secara terstruktur dan sistematis (Siewe dan Ngounou, 2025).

Tabel 2.6 Simbol-simbol activity diagram

Gambar	Nama	Keterangan
<img>Rectangle with rounded corners</img>	Aktivitas	Menunjukkan interaksi antarmuka kelas.
<img>Horizontal oval</img>	Action	Keadaan sistem yang menunjukkan pelaksanaan tindakan tertentu.
<img>Black circle</img>	Node Permulaan	Kondisi awal yang dicapai sistem ditunjukkan dalam diagram aktivitas sebagai kondisi awal.
<img>Black circle with a white border</img>	Aktivitas Node Akhir	Kondisi akhir yang dicapai sistem juga ditunjukkan dalam diagram aktivitas sebagai kondisi akhir.
<img>Horizontal line</img>	Node Cabang	Sebuah aliran yang akhirnya bercabang menjadi banyak aliran.
Page 82
<page_number>72</page_number>

Tabel 2.6 Simbol-simbol activity diagram (Lanjutan)

Gambar	Nama	Keterangan
<img>Keputusan</img>	Keputusan	Ketika ada lebih dari satu pilihan atau aktivitas, itu disebut asosiasi percabangan.
Class Diagram
UML class diagram merupakan diagram yang digunakan untuk memodelkan struktur statis suatu sistem dengan menampilkan kelas, atribut, operasi, serta hubungan antar kelas. Dalam rekayasa perangkat lunak berbasis model, diagram kelas banyak dimanfaatkan dalam berbagai proses seperti refactoring dan transformasi, termasuk untuk perbaikan desain, peningkatan keterpeliharaan, penerapan pola desain, hingga pembangkitan kode dan skema basis data. Untuk mengevaluasi sistem atau perangkat lunak yang memproses diagram kelas secara efektif, diperlukan cakupan berbagai variasi struktur diagram yang representatif. Salah satu pendekatan yang dapat digunakan adalah dengan mengelompokkan diagram ke dalam kelas-kelas kesetaraan struktural, sehingga pengujian dapat dilakukan secara efisien dengan memilih diagram perwakilan dari setiap kelompok. Pendekatan ini memungkinkan evaluasi yang lebih sistematis dan komprehensif terhadap kinerja serta ketahanan alat bantu rekayasa perangkat lunak yang berbasis UML (Tazin dan Kokar, 2025).

Tabel 2.7 Simbol – simbol class diagram

Gambar	Nama	Keterangan
<img>Package</img>	Package	Paket adalah kumpulan satu atau lebih kelas yang dikemas dalam satu paket.
<img>Kelas</img>	Kelas	Dalam struktur sistem, setiap kelas memiliki nama, set properti, dan set operasi atau metode.
Page 83
<page_number>73</page_number>

Tabel 2.7 Simbol – simbol class diagram (Lanjutan)

Gambar	Nama	Keterangan
<img>Antarmuka</img>	Antarmuka	Sama dengan prinsip pemrograman berorientasi objek.
<img>Hubungan</img>	Hubungan	Koneksi antara kelas-kelas yang tidak didefinisikan secara khusus.
<img>Hubungan berarah</img>	Hubungan berarah	Hubungan antara kelas yang mengindikasikan bahwa satu kelas digunakan oleh kelas lainnya.
<img>Generalisasi</img>	Generalisasi	Hubungan antar kelas yang mencerminkan hierarki umum-khusus.
<img>Kebergantungan</img>	Kebergantungan	Hubungan kelas menunjukkan bahwa dalam situasi tertentu, satu kelas membutuhkan kelas lainnya, menunjukkan ketergantungan antara kelas.
<img>Agregasi</img>	Agregasi	Keterkaitan antar kelas yang menggambarkan konsep keseluruhan-bagian, di mana satu kelas merupakan bagian dari atau terkait dengan keseluruhan yang lebih besar.
Sequence Diagram
Sequence diagram merupakan salah satu diagram perilaku dalam UML yang digunakan untuk menggambarkan interaksi antar objek serta pertukaran pesan yang terjadi seiring waktu. Diagram ini menunjukkan bagaimana peristiwa atau aktivitas dalam suatu use case dipetakan ke dalam operasi pada kelas-kelas yang terdapat pada class diagram. Sequence diagram banyak digunakan pada tahap perancangan

Page 84
<page_number>74</page_number>

rinci untuk memodelkan komunikasi antar objek secara terstruktur sesuai dengan kebutuhan sistem. Sifatnya yang intuitif dan mudah dipahami menjadikan diagram ini populer dalam membantu pengguna maupun pengembang memahami alur kerja sistem dan hubungan antar objek. Selain itu, sequence diagram juga dapat dimanfaatkan untuk menggambarkan alur pemanggilan metode, spesifikasi interaksi pada sistem terdistribusi, serta sebagai dasar dalam proses pengujian sistem (Al-Fedaghi, 2021).

Tabel 2.8 Simbol – simbol sequence diagram

Gambar	Nama	Keterangan
<img>A stick figure representing an actor.</img>	Aktor	Actor memiliki peran orang ketika berkomunikasi dengan sistem yang dibuat, bisa berupa individu, sistem lain, atau alat.
<img>A horizontal line with a vertical dashed line extending downwards, representing a lifeline.</img>	Jalur Eksistensi	Entitas objek, antarmuka yang berinteraksi dan berkomunikasi.
<img>A rectangle with an arrow pointing to another rectangle, representing an input message.</img>	Input Pesan	Menjelaskan interaksi antara item-item yang menyimpan detail tentang peristiwa yang terjadi.
<img>A rectangle with a dashed arrow pointing back to itself, representing a self-message.</img>	Message to Self	Menjelaskan interaksi objek dengan pemanggilan metode dan nilai balik yang menentukan kejadian yang terjadi.
2.24 Pengujian BlackBox

Pengujian blackbox merupakan metode pengujian perangkat lunak yang berfokus pada pengujian fungsi sistem tanpa melihat atau menganalisis struktur internal maupun kode program di dalamnya. Pengujian ini dilakukan dengan memeriksa kesesuaian antara masukan yang diberikan dan keluaran yang dihasilkan berdasarkan spesifikasi dan kebutuhan yang telah ditetapkan. Oleh karena itu, metode ini sangat sesuai digunakan pada pengujian tingkat tinggi ketika detail implementasi sistem tidak diketahui oleh penguji. Dalam pelaksanaannya,

Page 85
<page_number>75</page_number>

Pengujian blackbox memanfaatkan berbagai teknik seperti partisi ekivalensi, analisis nilai batas, pengujian tabel keputusan, dan pengujian transisi keadaan untuk mengidentifikasi kesalahan secara efektif. Metode ini dapat diterapkan pada berbagai tahapan pengujian perangkat lunak, antara lain pengujian unit, integrasi, sistem, penerimaan, regresi, dan fungsional (Edirisinghe dan Wickramaarachchi, 2024).

Page 86
BAB III METODOLOGI PENELITIAN

3.1 Metode Pengumpulan Data Dalam penelitian ini, terdapat beberapa teknik pengumpulan data yang diterapkan, antara lain sebagai berikut:

3.1.1 Akuisisi Dataset Publik (Open Source) Dataset sekunder diperoleh dari repositori terbuka yang kredibel untuk mendukung variasi data dalam penelitian ini. Fokus utama dari akuisisi ini adalah pada karakteristik visual dan keberagaman citra struk pembelian. Berikut adalah rincian dataset publik yang digunakan:

Dataset CORD-v2 Berdasarkan penelitian Park dkk., 2019, penelitian ini menggunakan versi publik dari dataset CORD yang terdiri dari 1.000 citra struk khusus kategori restoran di Indonesia. Citra pada dataset ini telah mengalami proses pengolahan di mana teks dan informasi selain daftar item serta informasi pembayaran telah dihilangkan atau dilakukan proses blurring. Hal ini menghasilkan dataset yang secara visual hanya menonjolkan bagian transaksi utama pada struk. Dataset ini diakses melalui repositori Oxen.ai.
Dataset SROIE v2 Dataset ini berasal dari kompetisi ICDAR 2019 on Scanned Receipt OCR and Information Extraction oleh Z. Huang dkk., 2019. Penelitian ini memanfaatkan 1.000 citra struk hasil pindaian (scanned receipts) sebagai basis data citra. Fokus penggunaan dataset ini adalah pada kualitas visual dokumen pindaian yang merepresentasikan format struk cetak standar, dan tersedia melalui platform Kaggle.
Dataset Nanonets Dikurasi oleh Mandal dkk., 2025 sebagai bagian dari platform IDPLeaderboard. Dataset ini digunakan sebagai referensi dalam evaluasi Intelligent Document Processing (IDP), khususnya pada kategori pengenalan
<page_number>68</page_number>

Page 87
<page_number>69</page_number>

informasi kunci atau Key Information Extraction (KIE) untuk struk pembelian. Data citra ini diakses melalui Hugging Face.

Dataset UniqueData Merupakan dataset OCR Receipts from Grocery Stores yang dikembangkan oleh UniData, 2026. Dataset ini berfokus pada deteksi teks pada struk toko kelontong (grocery stores) dengan kualitas citra yang dioptimalkan untuk pelatihan model AI di sektor ritel yang terdiri dari 20 citra. Dataset ini diperoleh melalui repositori Hugging Face.

Dataset Roboflow Bersumber dari repositori (Roboflow, 2024), dataset ini menyediakan koleksi citra struk belanja dengan karakteristik visual khusus berupa format grayscale (skala abu-abu) yang terdiri dari 1.719 citra. Penggunaan citra non-warna ini bertujuan untuk menguji performa model terhadap dokumen yang memiliki keterbatasan informasi kromatik (warna). Dataset ini diakses melalui platform Roboflow Universe.

Dataset ExpressExpense Dataset ini disediakan oleh ExpressExpense, 2026 melalui koleksi Sample Receipt Dataset (SRD). Data terdiri dari 200 citra struk restoran berkualitas tinggi dengan dimensi gambar yang tajam (lebih dari 600 piksel). Dataset ini digunakan untuk memperkaya variasi citra struk restoran dalam kondisi pencahayaan dan sudut pengambilan gambar yang ideal.

3.1.2 Pengumpulan Data Manual (Web Discovery)
Peneliti melakukan pencarian dan pengumpulan citra struk pembelian secara manual melalui Google Images dengan kata kunci “struk pembelian” untuk mendapatkan sampel visual struk dengan kondisi dan format yang beragam. Pengumpulan ini juga mencakup platform media sosial X (Twitter) dan Threads, yang sering digunakan pengguna untuk berbagi foto struk pembelian dalam konteks percakapan sehari-hari. Metode ini bertujuan untuk menangkap variasi struk yang tidak terwakili dalam dataset publik, khususnya struk dari merchant Indonesia dengan format dan tipografi yang bervariasi.

Page 88
<page_number>70</page_number>

3.1.3 Web Scraping (Pinterest)
Untuk memperkaya variasi visual dataset, dilakukan proses web scraping pada platform Pinterest dengan menggunakan kata kunci pencarian “struk pembelian”. Platform ini dipilih karena menyediakan koleksi foto struk yang diambil secara langsung menggunakan kamera ponsel (handheld) dengan berbagai variasi sudut pengambilan gambar (angle) yang tidak beraturan. Secara khusus, pengumpulan data melalui metode ini difokuskan pada citra yang memiliki format vertikal atau rasio aspek 9:16, yang merepresentasikan perilaku pengguna saat mendokumentasikan struk secara fisik. Variasi kondisi gambar, seperti sudut kemiringan yang ekstrem, kondisi pencahayaan yang bervariasi, serta tingkat kejelasan teks yang berbeda-beda, sangat krusial untuk meningkatkan ketahanan (robustness) model terhadap input dokumen berkualitas rendah dalam skenario penggunaan nyata.

3.1.4 Pengambilan Data Primer (Real-Life)
Data primer dikumpulkan langsung oleh peneliti melalui dokumentasi struk pembelian nyata dari transaksi sehari-hari guna memastikan dataset mengandung sampel yang representatif terhadap kondisi penggunaan sistem sebenarnya di Indonesia. Koleksi data ini mencakup struk fisik dari minimarket, restoran, dan toko ritel lokal dengan berbagai format sistem kasir konvensional, serta menyertakan e-receipt atau bukti bayar digital dari berbagai platform belanja daring dan layanan transportasi online yang saat ini umum digunakan. Dalam proses dokumentasi struk fisik, peneliti menggunakan perangkat iPhone 13 Pro untuk menjamin ketajaman resolusi dan keterbacaan teks pada citra digital, sehingga seluruh data primer baik dalam format cetak maupun digital memiliki kualitas yang optimal untuk diolah pada tahap penelitian selanjutnya.

Berikut merupakan contoh sampel dari berbagai kumpulan dataset struk pembelian yang ditampilkan pada Gambar 3.1 hingga Gambar 3.4.

Page 89
<page_number>71</page_number>

<img>Image of a person holding a shopping receipt and a plastic bag, with a shopping cart in the background.</img> (a)

<img>Image of a receipt from a store.</img> (b)

Gambar 3.1 Contoh gambar struk (a) Pinterest dan (b) CORD-v2

<img>Image of a digital receipt from Serba Serbi Jaya.</img> (c)

<img>Image of a receipt from Crisfield Seafood Restaurant.</img> (d)

<img>Image of a tax invoice from PASARAYA CINWA SDN BHD.</img> (e)

Gambar 3.2 Contoh gambar struk (c) Digital, (d) ExpressExpense, dan (e) Nanonets

Page 90
<page_number>72</page_number>

<img>Image of a receipt from Rincon Mexicano</img> (f) <img>Image of a receipt from Whole Foods Market</img> (g)

Gambar 3.3 Contoh gambar struk (f) Roboflow dan (g) UniqueData

<img>Image of a receipt from Indah Gift & Home Deco</img> (h) <img>Image of a receipt from Kochi Sorumba</img> (i) <img>Image of a receipt from Jakarta Selatan</img> (j)

Gambar 3.4 Contoh gambar struk (h) SROIE-v2, (i) Primary, dan (j) Threads

3.2 Metode Pengembangan Sistem

Dalam penelitian ini, digunakan metode pengembangan sistem Agile Scrum yang terdiri dari fase Pre-Game, Development (Sprint), dan Post-Game. Pemilihan Agile Scrum didasarkan pada sifat eksploratif penelitian ini, di mana komponen fine-tuning GLM-OCR, arsitektur Hierarchical Agent Teams, dan integrasi MCP memerlukan evaluasi iteratif dan penyesuaian berkelanjutan yang tidak dapat

Page 91
<page_number>73</page_number>

sepenuhnya direncanakan di awal. Berikut adalah rincian pelaksanaan setiap fase dalam konteks penelitian ini:

Pre-Game (Perencanaan) Pada fase ini dilakukan penyusunan kebutuhan sistem secara menyeluruh dan pembentukan product backlog. Aktivitas mencakup analisis kebutuhan fungsional dan non-fungsional sistem Agentic AI untuk data entry struk pembelian, penetapan arsitektur sistem secara high-level, penentuan komponen utama yang akan dikembangkan (GLM-OCR fine-tuning, LangGraph agent, MCP server, React Native frontend), serta prioritisasi item backlog berdasarkan dependensi teknis antar komponen.

Sprint 1 (Fine-Tuning dan Persiapan Data) Sprint pertama berfokus pada persiapan dataset fine-tuning dan pelatihan model GLM-OCR menggunakan LoRA via LLaMA Factory. Aktivitas mencakup pengumpulan dan anotasi dataset struk pembelian dari empat sumber (open-source, web discovery, scraping, dan data nyata), konfigurasi lingkungan pelatihan LLaMA Factory dengan parameter LoRA, pelaksanaan fine-tuning dengan target konsistensi output JSON schema, serta evaluasi awal hasil ekstraksi menggunakan metrik ANLS* dan KIEval.

Sprint 2 (Arsitektur Agentic dan MCP) Sprint kedua berfokus pada pembangunan arsitektur backend sistem. Aktivitas mencakup implementasi Hierarchical Agent Teams menggunakan LangGraph dengan supervisor agent, SQL agent, dan data entry team, implementasi MCP-SQLite dan MCP-GSheets beserta tool yang diperlukan, integrasi guardrails (Llama Guard 2 dan LLM-as-Judge), implementasi mekanisme HITL checkpoint sebelum operasi penulisan ke Google Sheets, serta evaluasi MCP tool accuracy mencakup AST dan Pass@K.

Sprint 3 (Frontend dan Integrasi Sistem) Sprint ketiga berfokus pada pengembangan antarmuka pengguna dan integrasi end-to-end seluruh komponen sistem. Aktivitas mencakup pengembangan antarmuka React Native dengan Expo untuk Android, iOS, dan Web, integrasi frontend dengan backend FastAPI, pengujian alur kerja end-to-end dari input struk

Page 92
<page_number>74</page_number>

hingga output Google Sheets, serta penyesuaian berdasarkan hasil pengujian integrasi.

Post-Game (Pengujian dan Finalisasi) Fase Post-Game mencakup pengujian sistem secara menyeluruh dan finalisasi dokumentasi. Aktivitas mencakup Black Box Testing terhadap seluruh fungsionalitas sistem, serta penyempurnaan sistem berdasarkan hasil evaluasi.
3.3 Waktu dan Tempat Penelitian 3.3.1 Waktu Waktu pelaksanaan penelitian berlangsung dari bulan Februari 2026 sampai April 2026 dengan rincian yang ditampilkan pada Tabel 3.1.

Tabel 3.1 Waktu penelitian

No.	Detail Kegiatan	Waktu Penelitian (2026)	Keterangan
Februari	Maret	April
1	2	3	4	1	2	3	4
1.	Pre-Game (Perencanaan & Backlog)									Product Backlog, Arsitektur Sistem
2.	Sprint 1 (Fine Tuning & Dataset)									Dataset, LoRA, LLaMA Factory, KIEval, ANLS*
3.	Sprint 2 (Agent & MCP)									LangGraph, MCP Server, Guardrails, AST, Pass@K
4.	Sprint 3 (Frontend & Integrasi)									React Native, Expo, Fast API
5.	Post-Game (Pengujian & Finalisasi)									Blackbox Testing, Evaluasi, Dokumentasi
Page 93
<page_number>75</page_number>

3.3.2 Tempat Penelitian
Penelitian tugas akhir ini bertempat di Laboratorium Computer Science & Artificial Intelligence, Jurusan Teknik Informatika, Fakultas Teknik, Universitas Halu Oleo.

3.4 Analisis Kebutuhan Sistem
Analisis kebutuhan sistem bertujuan untuk menetapkan spesifikasi yang diperlukan mulai dari tahap pengembangan hingga implementasi sistem. Analisis tersebut mencakup kebutuhan fungsional, yang terdiri atas input, proses, dan output, serta kebutuhan nonfungsional yang meliputi perangkat keras (hardware) dan perangkat lunak (software).

3.4.1 Analisis Kebutuhan Fungsional
Analisis kebutuhan fungsional bertujuan untuk mengidentifikasi fitur-fitur yang harus tersedia agar sistem dapat beroperasi sesuai tujuan penelitian, yaitu mengotomatisasi proses data entry dari struk pembelian menggunakan Vision Language Model ter-fine-tune dan orkestrasi hierarchical multi-agent berbasis MCP. Kebutuhan fungsional dalam penelitian ini dijabarkan dalam tiga kategori, yaitu kebutuhan masukan, kebutuhan proses, dan kebutuhan keluaran.

Kebutuhan Masukan (Input) Sistem menerima dua jenis masukan utama dari pengguna melalui antarmuka percakapan (chatbot). Jenis masukan pertama adalah dokumen struk pembelian dalam format citra digital (JPG, PNG) atau PDF, yang diunggah oleh pengguna melalui fitur attachment pada antarmuka chat. Dokumen tersebut dapat berupa foto struk fisik yang diambil menggunakan kamera ponsel, citra hasil pemindaian (scan), maupun e-receipt dalam format digital. Sistem mendukung pemrosesan dokumen PDF multi-halaman, di mana setiap halaman diperlakukan sebagai satu unit struk yang diproses secara independen. Jenis masukan kedua adalah pesan teks (text-only) yang dikirimkan oleh pengguna dalam mode percakapan, yang dapat berupa instruksi untuk melihat data hasil ekstraksi, permintaan untuk memasukkan data ke Google Sheets, klarifikasi terhadap hasil ekstraksi, atau pertanyaan terkait data yang telah tersimpan dalam sistem. Selain
Page 94
<page_number>76</page_number>

itu, pengguna juga memberikan masukan berupa konfirmasi atau koreksi pada checkpoint Human-in-the-Loop (HITL) sebelum operasi penulisan data dieksekusi.

Kebutuhan Proses (Process) Sistem melaksanakan serangkaian proses yang saling terkoordinasi untuk mentransformasi masukan menjadi keluaran yang diharapkan. Proses pertama adalah validasi keamanan melalui lapisan guardrails yang terdiri dari dua komponen paralel, yaitu deteksi prompt injection dan jailbreaking menggunakan model Llama Prompt Guard 2, serta penyaringan domain yang dilarang (blacklist) menggunakan pendekatan LLM-as-judge dengan model Gemini. Proses kedua adalah ekstraksi informasi kunci (Key Information Extraction) dari citra struk pembelian menggunakan model GLM-OCR 0,9B yang telah di-fine-tune dengan LoRA. Model ini menerima citra struk dan menghasilkan keluaran JSON terstruktur yang mencakup informasi toko (store name, location, contacts), daftar item beserta harga, serta ringkasan pembayaran (grand total, metode pembayaran, kembalian). Untuk dokumen PDF, setiap halaman dirender menjadi citra PNG pada resolusi 200 DPI sebelum diproses oleh model. Proses ketiga adalah penyimpanan hasil ekstraksi ke database SQLite sebagai single source of truth, yang mencakup metadata dokumen, data per halaman, dan riwayat percakapan. Proses keempat adalah orkestrasi oleh Supervisor Agent (Klaudia) yang menganalisis kebutuhan pengguna, mendelegasikan tugas ke sub-agent yang sesuai (SQL Agent untuk operasi database atau Data Entry Team untuk operasi Google Sheets), dan menyintesis hasil untuk dikembalikan kepada pengguna. Proses kelima adalah Human-in-the-Loop, yaitu konfirmasi dari pengguna sebelum Data Entry Team Agent melakukan penulisan data ke Google Sheets melalui MCP-GSheets. Proses keenam adalah operasi data entry otomatis ke Google Sheets, yang mencakup pembuatan sheet baru, penambahan baris data, dan pembaruan sel melalui tool yang diekspos oleh MCP-GSheets.

Kebutuhan Keluaran (Output) Sistem menghasilkan tiga jenis keluaran utama. Keluaran pertama adalah data terstruktur dalam format JSON yang tersimpan di database SQLite, mencakup

Page 95
<page_number>77</page_number>

hasil ekstraksi informasi kunci dari setiap halaman struk yang diproses. Keluaran kedua adalah data struk pembelian yang telah dientri secara otomatis ke Google Sheets, dengan struktur kolom yang sesuai dengan skema ekstraksi (informasi toko, daftar item, dan ringkasan pembayaran). Keluaran ketiga adalah respons percakapan dari Supervisor Agent Klaudia yang disampaikan melalui antarmuka chat, berupa ringkasan hasil pemrosesan, konfirmasi status data entry, jawaban atas pertanyaan pengguna, atau permintaan klarifikasi apabila terdapat ambiguitas dalam instruksi pengguna.

3.4.2 Analisis Kebutuhan Nonfungsional
Analisis Analisis kebutuhan nonfungsional meliputi evaluasi sumber daya dan lingkungan yang diperlukan untuk membangun sistem. Secara umum, kebutuhan ini terbagi menjadi kebutuhan perangkat keras (hardware) dan perangkat lunak (software), yang bertujuan memastikan sistem beroperasi efisien dan memenuhi standar yang ditetapkan.

Kebutuhan Perangkat Keras
Perancangan dan pembangunan sistem memerlukan perangkat keras sebagai media utama untuk implementasi dan operasional sistem agar berfungsi optimal. Rincian kebutuhan perangkat keras yang digunakan dalam pengembangan sistem ini tercantum pada Tabel 3.2.

Tabel 3.2 Spesifikasi perangkat keras

No.	Nama Perangkat	Spesifikasi
1.	Laptop	Macbook Air M2, 2022
2.	Processor	Chip Apple M2 CPU 8-core dan GPU 8-core
3.	Memory	RAM 16 GB
4.	Hardisk	256 GB
5.	Monitor	Liquid retina 13.6 inch
6.	Smartphone	iPhone 13 Pro
7.	Kamera	Pro 12MP camera system
8.	GPU	NVIDIA L4 (24 GB VRAM)
Page 96
<page_number>78</page_number>

Kebutuhan Perangkat Lunak Perancangan sistem memerlukan perangkat lunak sebagai komponen utama untuk mendukung implementasi dan operasional sistem yang dikembangkan. Rincian kebutuhan perangkat lunak untuk sistem ini disajikan pada Tabel 3.3.
Tabel 3.3 Spesifikasi perangkat lunak

No.	Nama	Fungsi	Spesifikasi
1.	MacOS	Sistem operasi pengembangan utama	Sequioia 15.6
2.	Python	Bahasa pemrograman backend dan AI	Python 3.13
3.	React Native & Expo	Framework pengembangan aplikasi mobile	Expo SDK 55, React Native 0.83
4.	FastAPI	Pembangunan web service API	FastAPI 0.115
5.	Langchain	Framework pengelolaan rantai LLM	Langchain 0.3.20
6.	LangGraph	Orkestrasi Multi-Agent System (MAS)	LangGraph 0.3.30
7.	FastMCP	Implementasi MCP	FastMCP 0.5.0
8.	LLaMA Factory	Alat fine-tuning model GLM-OCR	Llamafactory 0.9.4
9.	Groq	Inference engine guardrails	Groq 0.9
10.	vLLM	Inference engine GLM-OCR secara lokal/server	vLLM 0.19.0
11.	Hugging Face	Repositori model dan dataset	Hugging Face Hub 1.4.1
12.	Kaggle & Roboflow	Sumber akuisisi dataset sekunder	Kaggle 1.0.0, Roboflow 1.1.4
Page 97
<page_number>79</page_number>

Tabel 3.3 Spesifikasi perangkat lunak (Lanjutan)

No.	Nama	Fungsi	Spesifikasi
13.	Oxen.ai	Versioning dataset	Oxen 0.44.2
14.	Github & Git	Sistem kontrol versi code	Git 2.42.0
15.	MlFlow	Tracking metrics logs	MlFlow 3.11.1
16.	Langfuse	Tracing AI agent	Layanan Cloud
17.	Label Studio	Alat anotasi dataset	Label Studio 1.22.0
18.	Lightning AI	Infrastruktur GPU cloud	PyTorch Lightning 2.6.1
19.	Visual Studio Code	Integrated Development Environment (IDE)	VS Code 1.105.1
20.	Xcode	Compiler emulator iOS	Xcode 26.4
21.	Google Sheets	Media output	Layanan Cloud
22.	SQLite	Basis data lokal sistem	SQLite 0.20.0
3.5 Analisis Perancangan Sistem

Perancangan sistem ini mencakup empat komponen utama, yaitu flowchart, Unified Modeling Language (UML), antarmuka pengguna (UI), dan skenario pengujian. Flowchart digunakan untuk menggambarkan alur logika dan proses utama dari masukan hingga keluaran. UML digunakan untuk memodelkan interaksi antar komponen sistem melalui diagram use case, activity, class, dan sequence. Perancangan antarmuka menggambarkan tampilan visual yang akan digunakan pengguna untuk berinteraksi dengan sistem. Skenario pengujian mendefinisikan prosedur evaluasi yang mencakup perhitungan metrik secara matematis dan pengujian fungsionalitas blackbox.

3.5.1 Flowchart

Flowchart sistem pada Gambar 3.5 menggambarkan alur kerja keseluruhan dari sistem pemrosesan struk berbasis agen yang dirancang dalam penelitian ini. Alur dimulai ketika pengguna mengirimkan permintaan melalui antarmuka percakapan, baik berupa pesan teks maupun dokumen lampiran. Sebelum

Page 98
<page_number>80</page_number>

permintaan tersebut diproses lebih lanjut, setiap masukan yang diterima diwajibkan melewati lapisan Guardrails terlebih dahulu. Lapisan ini menggunakan kombinasi Llama Prompt Guard 2 dan mekanisme LLM-as-judge untuk mendeteksi potensi ancaman seperti prompt injection, konten berbahaya, serta topik yang berada di luar cakupan sistem. Apabila permintaan tidak lolos validasi, sistem secara langsung mengembalikan pesan penolakan kepada pengguna tanpa meneruskan proses ke komponen berikutnya.

Setelah melewati lapisan guardrails, sistem melakukan pemeriksaan kondisi untuk menentukan jalur pemrosesan yang sesuai berdasarkan jenis masukan yang diterima. Apabila pengguna mengunggah dokumen berupa PDF atau gambar, Extraction Agent memanfaatkan model GLM-OCR yang telah disesuaikan melalui fine-tuning untuk mengekstraksi informasi struk secara langsung dalam bentuk JSON terstruktur. Hasil ekstraksi selanjutnya divalidasi dan digabungkan ke dalam skema baku yang telah ditentukan sebelumnya.

Dalam kondisi di mana pengguna meminta proses data entry ke Google Sheets, baik setelah pemrosesan dokumen maupun melalui permintaan teks eksplisit, sistem menerapkan mekanisme Human-in-the-Loop (HITL) sebagai langkah konfirmasi sebelum eksekusi penulisan data dilakukan. Supervisor Agent menampilkan pratinjau data yang akan dimasukkan dan meminta persetujuan eksplisit dari pengguna terlebih dahulu. Apabila pengguna menyetujui, tugas penulisan didelegasikan kepada Data Entry Team yang terdiri dari tiga sub-agen terkoordinasi, yaitu Read Agent, Sheet Agent, dan Write Agent, yang mengeksekusi operasi penulisan secara terstruktur melalui MCP-GSheets. Sebaliknya, apabila pengguna menolak atau memberikan koreksi terhadap data yang ditampilkan, sistem mengembalikan alur ke tahap perbaikan data sebelum proses konfirmasi diulang kembali. Pendekatan ini memastikan bahwa tidak ada data yang dituliskan ke Google Sheets tanpa validasi eksplisit dari pengguna, sehingga integritas data dapat terjaga sepanjang siklus operasional sistem. Gambar 3.5 menunjukkan visual alur flowchart bagaimana sistem Klaudia bekerja.

Page 99
<page_number>81</page_number>

<img>Flowchart of the main Klaudia system process, starting with "User mengirim pesan" and ending with "Respons ke User". The flow includes decision points for attachments, guardrails, and data entry, with various processing steps like PDF/Image conversion, extraction, validation, and user confirmation.</img>

Gambar 3.5 Flowchart alur sistem utama Klaudia

Page 100
<page_number>82</page_number>

3.5.2 Perancangan Unified Modeling Language (UML)
Sistem ini dirancang menggunakan Unified Modeling Language (UML), sebuah bahasa visual yang digunakan untuk memodelkan dan mengkomunikasikan suatu sistem melalui berbagai diagram. Empat jenis diagram UML yang digunakan dalam perancangan sistem ini meliputi use case diagram, activity diagram, class diagram, dan sequence diagram.

Use Case Diagram

Use case diagram menggambarkan interaksi antara aktor User (pengguna) dengan sistem Klaudia. Dalam diagram ini, batas sistem (system boundary) Klaudia terbagi menjadi dua kelompok use case.

Kelompok pertama adalah User Cases yang merepresentasikan enam fungsi yang dapat diakses langsung oleh pengguna, yaitu upload struk pembelian dalam format PDF atau citra, kirim pesan teks sebagai instruksi atau pertanyaan, lihat hasil ekstraksi struk yang telah diproses, minta data entry ke Google Sheets, konfirmasi atau koreksi data pada checkpoint Human-in-the-Loop (HITL), serta kelola sesi percakapan.

Kelompok kedua adalah Internal Process yang merepresentasikan lima proses otonom yang dieksekusi oleh sistem tanpa intervensi langsung pengguna, yaitu validasi guardrails untuk menyaring masukan yang tidak aman, ekstraksi KIE menggunakan GLM-OCR fine-tuned, orkestrasi agent oleh Supervisor Klaudia, context enrichment untuk menginjeksi informasi file aktif ke dalam konteks percakapan, query database melalui MCP-SQLite, serta tulis ke spreadsheet melalui MCP-GSheets. Hubungan antar kedua kelompok direpresentasikan melalui relasi include dan extend, di mana setiap use case pengguna memicu satu atau lebih proses internal secara otomatis. Use case diagram sistem Klaudia dapat dilihat pada Gambar 3.6.

Page 101
<page_number>83</page_number>

<img>Use case diagram for Klaudia system showing user interactions with system cases and internal processes.</img>

Gambar 3.6 Use case diagram sistem Klaudia

Activity Diagram
Activity diagram menggambarkan alur aktivitas dari sisi pengguna dan sistem secara bersamaan menggunakan swimlane. Diagram ini dibagi menjadi dua bagian untuk mengakomodasi kompleksitas alur kerja sistem secara keseluruhan.

Bagian pertama merepresentasikan proses validasi masukan dan guardrails dengan dua swimlane, yaitu Pengguna dan Backend. Alur dimulai dari pengguna yang mengunggah struk atau mengirim pesan, kemudian FastAPI menerima request dan menjalankan lapisan guardrails. Pada tahap ini, dua komponen validasi dieksekusi secara paralel melalui mekanisme fork, yaitu Llama Prompt Guard 2 untuk deteksi prompt injection dan LLM-as-Judge untuk penyaringan domain yang dilarang. Kedua hasil validasi disinkronisasi melalui join, kemudian decision node menentukan apakah masukan aman atau tidak. Apabila tidak aman, pesan penolakan dikembalikan ke pengguna dan alur berakhir. Apabila aman, alur dilanjutkan ke proses routing dan ekstraksi. Alur proses validasi masukan dan guardrails ditunjukkan pada Gambar 3.7.

Page 102
<page_number>84</page_number>

<img> A swimlane diagram with two lanes: "Pengguna" (User) and "Backend". The "Pengguna" lane starts with a black circle, leading to a rectangle labeled "User mengunggah struk / mengirim pesan". This connects to the "Backend" lane. The "Backend" lane starts with a rectangle "FastAPI menerima request", which leads to a pink rectangle "Jalankan Guardrails". From "Jalankan Guardrails", the flow splits into two parallel paths, separated by a thick horizontal line:

A rectangle "Llama Prompt Guard 2".
A rectangle "LLM-as-Judge (Blacklist Domain)". These two paths converge into a diamond shape labeled "Aman?". From the "Aman?" diamond, there are two paths:
If "Tidak aman", the flow goes to a pink rectangle "Tolak & kembalikan pesan error" in the "Pengguna" lane, which then leads to a black circle, ending the process.
If "Aman", the flow goes to a rectangle "Routing & Ekstrasi" in the "Backend" lane. </img>
Gambar 3.7 Activity diagram proses validasi masukan dan guardrails

Bagian kedua merepresentasikan proses routing, ekstraksi, orkestrasi agent, dan data entry dengan tiga swimlane, yaitu Pengguna, Backend, dan Klaudia. Alur dimulai dari masukan yang telah tervalidasi aman, kemudian decision node menentukan apakah terdapat attachment dokumen atau hanya pesan teks. Apabila terdapat attachment, citra dikonversi ke format base64 PNG dan diproses oleh GLM-OCR untuk menghasilkan JSON terstruktur yang disimpan ke SQLite. Apabila hanya pesan teks, alur langsung menuju context enrichment. Selanjutnya, Supervisor Agent menganalisis intent pengguna dan mendelegasikan tugas ke SQL Agent untuk query data atau menampilkan pratinjau data kepada pengguna untuk konfirmasi HITL. Apabila pengguna mengonfirmasi, Data Entry Team yang terdiri dari Read Agent, Sheet Agent, dan Write Agent mengeksekusi operasi penulisan ke Google Sheets melalui MCP-GSheets. Apabila pengguna mengoreksi data, alur

Page 103
<page_number>85</page_number>

kembali ke pratinjau hingga konfirmasi diperoleh. Alur proses routing, ekstraksi, dan orkestrasi data entry ditunjukkan pada Gambar 3.8.

flowchart TD
    subgraph Pengguna
        A[User mengunggah struk / mengirim pesan]
        B[User meninjau hasil ekstraksi]
        C[Setuju?]
        D[User mengoreksi data]
        E[User menerima konfirmasi data entry]
        F[User menerima konfirmasi data entry]
    end

    subgraph Backend
        G[Input Aman Tervalidasi]
        H{Ada attachment?}
        I[Konversi PDF/ Image: base64 PNG]
        J[GLM-OCR: JSON extraction]
        K[Validasi schema & simpan ke SQLite]
        L[Context enrichment: inject file info]
    end

    subgraph Klaudia
        M[Analisis intent pengguna]
        N{Delegasi ke?}
        O[Read Agent: cek spreadsheet]
        P[Sheet Agent: buat sheet baru]
        Q[Write Agent: append rows via MCP-GSheets]
        R[Konfirmasi berhasil ke Supervisor]
        S[SQL Agent: query MCP-SQLite]
    end

    A --> G
    G --> H
    H -- Ada attachment --> I
    I --> J
    J --> K
    K --> L
    L --> M
    M --> N
    N -- Data entry --> B
    B --> C
    C -- Ya --> O
    C -- Tidak --> D
    D --> B
    N -- Query data --> S
    S --> R
    R --> E
    H -- Teks saja --> L
Gambar 3.8 Activity diagram proses routing, ekstraksi, dan orkestrasi data entry

Page 104
<page_number>86</page_number>

Class Diagram
Class diagram menggambarkan struktur statis sistem dengan menampilkan kelas-kelas utama beserta atribut, operasi, dan hubungan antar kelas. Diagram ini dibagi menjadi tiga bagian berdasarkan domain tanggung jawab masing-masing kelompok kelas.

Bagian pertama menggambarkan model data pengguna dan dokumen yang tersimpan dalam database SQLite. Kelas User memiliki relasi komposisi satu-ke-banyak terhadap kelas Session, di mana setiap sesi mengandung beberapa Conversation dan dapat mereferensikan satu atau lebih MetadataFile. Setiap MetadataFile terdiri dari satu atau lebih Page yang menyimpan hasil ekstraksi dalam format JSON. Kelas ExtractionAgent memiliki relasi dependensi terhadap MetadataFile dan Page, karena agent ini memproses dokumen dan memperbarui data halaman hasil ekstraksi. Class diagram model data pengguna dan dokumen ditunjukkan pada Gambar 3.9

<img> A class diagram showing the relationships between several classes: User, Session, MetadataFile, Conversation, Page, and ExtractionAgent. The User class has an integer id, username, email, passwordHash, createdAt, and lastLogin. It has methods authenticate() and createSession(). The Session class has an integer id, sessionName, createdAt, and updatedAt. It has methods addMessage() and attachFile(). The MetadataFile class has an integer id, type, totalPages, fileName, status, and createdAt. It has a method updateStatus(). The Conversation class has an integer id, sender, messageText, and timestamp. It has a method getReferencedFile(). The Page class has an integer id, pageNumber, agentExtractedText, status, and statusMessage. It has a method updateExtractedData(). The ExtractionAgent class has a vllmEndpoint, model, and methods processDocument() and runOCRExtraction(). Relationships include: User owns Session, Session contains Conversation, Session references MetadataFile, MetadataFile uploads Page, MetadataFile attaches Page, Page consists of MetadataFile, and ExtractionAgent processes MetadataFile and updates Page. </img>

Gambar 3.9 Class diagram model data pengguna dan dokumen

Page 105
<page_number>87</page_number>

Bagian kedua menggambarkan komponen guardrails yang bertanggung jawab atas validasi keamanan masukan. Kelas Guardrails Layer memiliki relasi komposisi terhadap dua kelas pelaksana, yaitu PromptGuardDetector yang mendeteksi prompt injection dan jailbreaking, serta BlacklistJudge yang mengevaluasi apakah masukan termasuk domain yang dilarang. Kedua komponen dieksekusi secara paralel oleh GuardrailsLayer. Class diagram komponen guardrails ditunjukkan pada Gambar 3.10.

<img> graph TD A[GuardrailsLayer] --> B(PromptGuardDetector) A --> C(BlacklistJudge) A -- executes --> B A -- executes --> C B -- + detect(text: String) : Boolean B -- - String modelName C -- + evaluate(text: String) : Boolean C -- - String IlmModel C -- - List domains A -- + validate(messageText: String) : Boolean </img>

Gambar 3.10 Class diagram komponen guardrails

Bagian ketiga menggambarkan hierarki agent dan integrasi MCP server. Kelas SupervisorAgent mengorkestrasikan SQLAgent dan DataEntryTeam melalui pola Hierarchical Agent Teams pada LangGraph. DataEntryTeam memiliki relasi komposisi terhadap tiga sub-agent spesialis, yaitu ReadAgent untuk pembacaan data spreadsheet, SheetAgent untuk pengelolaan tab sheet, dan WriteAgent untuk operasi penulisan data. SQLAgent mengeksekusi tool melalui MCPSQLite, sedangkan DataEntryTeam mengeksekusi tool melalui MCPGSheets, di mana relasi tool execution merepresentasikan batas eksekusi agent-tool yang distandarkan oleh Model Context Protocol. Class diagram hierarki agent dan MCP server ditunjukkan pada Gambar 3.11.

Page 106
<page_number>88</page_number>

<img> A class diagram showing the hierarchy of agents and the MCP server. The diagram includes the following classes:

SupervisorAgent: with attributes String IlmModel, String persona, and methods + analyzeIntent(text: String), + delegateTask(task: String).
SQLAgent: with attributes Object mcpSqliteClient, + getDocument(docId: Integer), + listPages(docId: Integer).
MCPGSheets: with attributes Integer port, String credentialsPath, and method + callSheetAPI(endpoint: String).
DataEntryTeam: with attribute Object mcpGSheetsClient, and method + coordinateTeam().
MCPSQLite: with attributes Integer port, String dbPath, and method + executeQuery(sql: String).
ReadAgent: with methods + listSheets(), + getSpreadsheetInfo().
WriteAgent: with methods + updateCells(range: String, values: List), + appendRows(sheetId: String, data: List).
SheetAgent: with methods + createSheet(name: String), + deleteSheet(id: String).
The relationships are:

SupervisorAgent orchestrates SQLAgent and DataEntryTeam.
DataEntryTeam manages ReadAgent, WriteAgent, and SheetAgent.
MCPGSheets is connected to DataEntryTeam via tool_execution.
SQLAgent is connected to MCPSQLite via tool_execution. </img>
Gambar 3.11 Class diagram hierarki agent dan MCP server

Sequence Diagram Sequence diagram menggambarkan interaksi antar objek serta pertukaran pesan secara kronologis untuk skenario utama sistem. Diagram ini dibagi menjadi tiga bagian yang merepresentasikan tiga fase utama dalam alur kerja end-to-end.
Bagian pertama menggambarkan fase upload dokumen dan ekstraksi informasi. Alur dimulai dari pengguna yang mengunggah struk melalui frontend React Native, kemudian FastAPI menerima request dalam format multipart yang berisi file dokumen beserta pesan teks, dan meneruskan masukan ke lapisan Guardrails untuk validasi keamanan. Setelah masukan dinyatakan aman oleh kedua komponen guardrails yang berjalan secara paralel, Extraction Agent menerima dokumen dan melakukan konversi ke format base64 PNG pada resolusi 200 DPI apabila dokumen berupa PDF multi-halaman. Citra yang telah dikonversi dikirimkan ke GLM-OCR melalui endpoint vLLM beserta prompt skema JSON, dan model menghasilkan keluaran JSON terstruktur yang mencakup informasi

Page 107
<page_number>89</page_number>

toko, daftar item, serta ringkasan pembayaran. Hasil ekstraksi kemudian divalidasi terhadap skema yang telah didefinisikan, di mana field yang hilang diisi dengan nilai default (string kosong untuk teks, array kosong untuk daftar), dan data yang telah tervalidasi disimpan ke tabel pages pada database SQLite beserta pembaruan status pada tabel metadata_file. Supervisor Agent selanjutnya menerima konteks file yang diinjeksikan ke dalam system prompt melalui mekanisme context enrichment, dan menghasilkan respons ringkasan hasil pemrosesan yang di-stream kepada pengguna melalui antarmuka percakapan. Sequence diagram fase upload dan ekstraksi ditunjukkan pada Gambar 3.12.

sequenceDiagram
    participant User
    participant FastAPI
    participant Guardrails
    participant ExtractionAgent
    participant GLMOCR
    participant SQLiteDB
    participant Supervisor

    User->>FastAPI: Upload struk (PDF/Image) + pesan
    FastAPI->>Guardrails: Validasi (Prompt Guard + LLM Judge)
    Guardrails-->>FastAPI: PASS
    FastAPI->>ExtractionAgent: process_document(file, metadata_id)
    ExtractionAgent-->>SQLiteDB: POST image + JSON schema prompt
    SQLiteDB-->>ExtractionAgent: Structured JSON
    ExtractionAgent-->>SQLiteDB: INSERT pages + UPDATE metadata_file
    SQLiteDB-->>User: (status: success, pages: n)
    User-->>FastAPI: Stream response
    FastAPI-->>Supervisor: Invoke + inject file context
    Supervisor-->>FastAPI: "Struk diproses! n item ditemukan."
Gambar 3.12 Sequence diagram proses upload struk hingga data entry ke Google Sheets

Bagian kedua menggambarkan fase permintaan data entry dan konfirmasi HITL. Pengguna mengirimkan instruksi berupa pesan teks untuk memasukkan data hasil ekstraksi ke Google Sheets, yang setelah melewati validasi guardrails, diteruskan ke Supervisor Agent melalui mekanisme invoke pada graf LangGraph. Supervisor menganalisis intent pengguna dan mendelegasikan pengambilan data ke SQL Agent, yang memanggil tool get_extraction melalui MCP-SQLite untuk mengambil JSON hasil ekstraksi dari tabel pages berdasarkan page_id yang direferensikan. Data yang diperoleh dikembalikan ke Supervisor, yang kemudian

Page 108
<page_number>90</page_number>

memformat data tersebut menjadi tabel pratinjau yang mudah dibaca oleh pengguna, mencakup kolom-kolom seperti nama item, kuantitas, harga satuan, dan total harga. Mekanisme interrupt pada LangGraph diaktifkan pada titik ini, yang menghentikan sementara eksekusi graf dan mengirimkan pratinjau data beserta permintaan konfirmasi kepada pengguna sebelum operasi penulisan yang bersifat irreversible dilaksanakan. Pendekatan ini memastikan bahwa tidak ada data yang ditulis ke Google Sheets tanpa persetujuan eksplisit dari pengguna, sesuai dengan prinsip Human-in-the-Loop yang diterapkan dalam arsitektur sistem. Sequence diagram fase permintaan data entry dan HITL ditunjukkan pada Gambar 3.13.

sequenceDiagram
    participant User
    participant FastAPI
    participant Guardrails
    participant Supervisor
    participant SQLAgent
    participant SQLiteDB

    User->>FastAPI: "Masukkan data ke Google Sheets"
    FastAPI->>Guardrails: Validasi input
    Guardrails-->>FastAPI: PASS
    FastAPI->>Supervisor: Invoke graph
    Supervisor-->>SQLAgent: Delegasi: ambil data ekstraksi
    SQLAgent-->>SQLiteDB: get_extraction(page_id=1)
    SQLiteDB-->>SQLAgent: extraction JSON
    SQLAgent-->>Supervisor: Return data
    Supervisor-->>FastAPI: INTERRUPT - pratinjau tabel + "Konfirmasi?"
    FastAPI-->>User: Tampilkan pratinjau + tombol konfirmasi
Gambar 3.13 Sequence diagram fase permintaan data entry dan HITL

Bagian ketiga menggambarkan fase konfirmasi pengguna dan penulisan data ke Google Sheets. Setelah pengguna mengonfirmasi, Supervisor Agent melanjutkan eksekusi graf dari titik interrupt dan mendelegasikan tugas penulisan ke Data Entry Team. Tim ini secara berurutan memanggil tool MCP-GSheets untuk memeriksa daftar sheet yang tersedia, membuat tab sheet baru apabila diperlukan, dan menambahkan baris data hasil ekstraksi. Konfirmasi keberhasilan dikembalikan melalui Supervisor ke pengguna. Sequence diagram fase konfirmasi dan penulisan ke Google Sheets ditunjukkan pada Gambar 3.14.

Page 109
<page_number>91</page_number>

<img>Sequence diagram showing the interaction between User, FastAPI, Supervisor, Data Entry Team, MCP-GSheets, and Google Sheets. The diagram illustrates the process of confirmation and writing data to Google Sheets, including steps like "Ya, konfirmasi", "Resume dari interrupt point", "Delegasi: tulis ke Sheets", "list_sheets(spreadsheet_id)", "GET metadata", "create_sheet("Store_A")", "POST batchUpdate", "append_rows(values)", "POST values:append", and "n baris berhasil".</img>

Gambar 3.14 Sequence diagram fase konfirmasi dan penulisan ke Google Sheets

3.5.3 Perancangan LLMOps Pipeline
Sistem Klaudia dirancang menggunakan pendekatan end-to-end LLMOps (Large Language Model Operations) yang mengintegrasikan seluruh tahapan mulai dari akuisisi data hingga inferensi produksi dalam satu kerangka kerja yang terstruktur. Pipeline ini terdiri dari empat komponen utama yang saling terhubung, yaitu Data Pipeline, Training Pipeline, Inference Pipeline, dan Klaudia Pipeline. Data Pipeline mencakup seleksi citra struk dari delapan sumber dataset, ekstraksi teks menggunakan GLM-OCR, anotasi terstruktur berbantuan Gemini 3.1 Pro, koreksi manual melalui Label Studio, serta penyimpanan versi dataset pada Oxen.ai dalam format ShareGPT. Training Pipeline mengelola eksperimen fine-tuning GLM-OCR dengan LoRA menggunakan LLaMA-Factory, pencarian hyperparameter heuristic dengan $r \in {8, 16, 32, 64}$ dan $\alpha = 2r$, pelacakan metrik KIEval, ANLS*, dan digit accuracy melalui MLflow, serta registrasi model terbaik ke Model Registry berbasis HuggingFace dan vLLM.

Page 110
<page_number>92</page_number>

Inference Pipeline mengemas layanan dalam kontainer Docker yang terdiri dari Klaudia Server dan GLM-OCR Server, dengan antrian asinkron berbasis Redis untuk menangani dokumen multi-halaman tanpa memblokir REST API. Klaudia Pipeline merepresentasikan lapisan orkestrasi agen hierarkis yang memvalidasi masukan melalui Guardrails, kemudian mendistribusikan tugas kepada Extraction Agent, SQL Agent, serta Data Entry Team yang terdiri dari Read Agent, Sheet Agent, dan Write Agent melalui Supervisor Agent. Seluruh operasi penulisan ke SQLite dan Google Sheets dilakukan eksklusif melalui MCP Server sebagai batas eksekusi terstandarkan, dengan mekanisme Human-in-the-Loop sebagai titik konfirmasi sebelum operasi irreversible dieksekusi. Komponen observabilitas menggunakan Lanfuse untuk pemantauan agent dan MinIO sebagai penyimpanan objek untuk artefak citra dan model, sebagaimana ditunjukkan pada Gambar 3.15

<img>Diagram of the Klaudia system pipeline, showing data flow from receipt data sources through image selection, data pipeline, Klaudia pipeline, training pipeline, and inference pipeline. The diagram includes components like HuggingFace, Kaggle, Roboflow, Oxen.ai, Pinterest, Thread & X, Primary, Image Selection, Raw OCR, Gemini 3.1 Pro, JSON, Human Correction, ShareGPT, Label Studio, OXEN.AI, User, Guardrails, Unstructured Docs, Extraction Agent, Single Source Database, Data Entry Team, Supervisor Agent, Human in the Loop, SQL Agent, Read Agent, Sheet Agent, Write Agent, Google Sheet, MCP Server, mlflow, Experiment Tracking, ANLS*, KIEval, Digit Accuracy, LLaMA-Factory, Hyperparameter Search Heuristic, LoRA Rank: r = [8, 16, 32, 64], alpha = r*2, Best Model, Observability Agents, Lanfuse, Model Registry, Object Storage, MinIO, Inference Pipeline, docker, Klaudia Server, GLM-OCR Server, REST API, Queue, "Input the receipt...", "Generated ouput...".</img>

Gambar 3.15 End-to-end LLMOps pipeline sistem Klaudia

Page 111
<page_number>93</page_number>

3.5.4 Perancangan Antarmuka
Antarmuka pengguna sistem Klaudia dirancang menggunakan React Native dengan Expo sebagai framework pengembangan lintas platform, dengan fokus implementasi pada versi mobile iOS. Pemilihan platform iOS didasarkan pada kesesuaian dengan perangkat yang digunakan selama proses penelitian, yaitu MacBook Air M2 sebagai lingkungan pengembangan utama, yang menjamin konsistensi antara perangkat pengembangan dan pengujian. Antarmuka terdiri dari tiga halaman utama, halaman pertama adalah AI Chat, yang berfungsi sebagai antarmuka percakapan utama antara pengguna dan Supervisor Agent Klaudia. Halaman kedua adalah Laporan Struk, yang menampilkan WebView berbasis Expo React Native yang terhubung secara real-time dengan Google Sheets, memungkinkan pengguna memantau dan memverifikasi data struk yang telah dientry oleh Data Entry Team Agent tanpa perlu berpindah ke aplikasi Google Sheets secara terpisah. Halaman ketiga adalah Profile, yang menyediakan informasi akun pengguna, pengaturan sistem, serta riwayat aktivitas, seperti Gambar 3.16.

<img>Three smartphone screens showing the Klaudia app interface. The left screen shows an AI Chat with a receipt image. The middle screen shows a Laporan Struk (Receipt Report) with a table of data. The right screen shows a Profile page with user information and settings.</img>

Gambar 3.16 Rancangan antarmuka pengguna sistem Klaudia

Page 112
<page_number>94</page_number>

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

Page 113
<page_number>95</page_number>

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

Page 115
<page_number>97</page_number>

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

Page 116
<page_number>98</page_number>

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
Page 117
<page_number>99</page_number>

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

Page 118
<page_number>100</page_number>

pertama (INDOMIE KALDU AYAM vs INDOMIE KALDU AYA) dan kesalahan digit pada harga item ketiga (8.600 vs 8.500).

B.2. Perhitungan Manual ANLS* ANLS* mengevaluasi kualitas ekstraksi informasi kunci dengan mengukur kemiripan karakter secara kontinu menggunakan Normalized Levenshtein Similarity (NLS). Berbeda dengan KIEval yang menggunakan exact match, ANLS* memberikan nilai parsial untuk prediksi yang hampir benar sehingga lebih toleran terhadap kesalahan penulisan minor akibat proses OCR. Metrik ini mendukung tipe data String, List, Dict, Tuple, dan None secara rekursif, sehingga mampu mengevaluasi struktur bersarang (nested) secara menyeluruh. Secara formal, ANLS* sesuai dengan persamaan (2.26).

Berdasarkan contoh pada Gambar 3.17, struktur data yang dievaluasi direpresentasikan sebagai pohon hierarki dapat digambarkan pada Gambar 3.18 sebagai berikut.

<img>Diagram of a tree structure representing data hierarchy. The root node is "Dict". It has two children: "payment Dict" and "items List". The "payment Dict" node has three children: "7", "29.500", and "29.500". The "items List" node has three children: "Dict", "Dict", and "Dict". The first "Dict" node has two children: "INDOMIE KALDU AYA" and "2". The second "Dict" node has two children: "7.000" and "INDOMIE RASA COTO". The third "Dict" node has two children: "4", "14.000", "ULTRA MILK LOW FA", "1", and "8.500".</img>

Gambar 3.20 Struktur pohon hierarki dari contoh ilustrasi Gambar 3.17

Page 119
<page_number>101</page_number>

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

Page 121
<page_number>103</page_number>

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
Hasil perhitungan sesuai rumus (2.26) menunjukkan bahwa model memperoleh nilai ANLS* sebesar 0,979 (97,9%). Nilai ini lebih tinggi dibandingkan KIEval Entity F1 (0,833) karena ANLS* memberikan skor parsial pada field yang hampir benar. Secara khusus, kesalahan pada item_name baris 1 (AYAM vs AYA) tidak dinolkan melainkan mendapat skor 0,944, dan kesalahan digit pada total_price baris 3 (8.600 vs 8.500) mendapat skor 0,800. Kedua kondisi ini masih berada di atas ambang batas τ = 0,5 , sehingga skor parsial tetap diberikan. Hal ini mencerminkan karakteristik ANLS* yang lebih toleran terhadap

Page 122
<page_number>104</page_number>

kesalahan minor akibat proses OCR pada model kecil seperti GLM-OCR 0.9B. Rangkuman hasil perhitungan ANSL* dapat dilihat pada Tabel 3.11.

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
Page 123
<page_number>105</page_number>

Tabel 3.12 Field harga evaluasi digit accuracy (Lanjutan)

Kategori	Field	Keterangan
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
Page 124
<page_number>106</page_number>

Tabel 3.13 Perbandingan hasil normalisasi (Lanjutan)

Field	d(v*)	d(v̂)	Cocok
items[1].unit_price	9000	2000	Tidak
items[1].total_price	9000	9000	Ya
payment.subtotal_price	34000	34000	Ya
payment.grand_total	34000	34500	Tidak
payment.tendered	50000	50000	Ya
payment.change	16000	16000	Ya
Kemudian akumulasi statistik. Total field yang dievaluasi (|F| dengan d(v*) ≠ Ø) = 8. Total field yang cocok secara digit = 6. Kemudian perhitungan Digit Accuracy pada sampel tunggal ini sebagai berikut. DA = $\frac{6}{8} \times 100% = 75,00%$

Perbandingan dengan skor ANLS* pada field yang sama. Perlu dicatat bahwa items[1].unit_price dengan prediksi "2.000" versus ground truth "9.000" menghasilkan LD = 1, sehingga NLS = 1/5 = 0,20 dan skor ANLS* parsial = 0,80. Dengan kata lain, ANLS* masih memberikan kredit parsial sebesar 0,80 pada prediksi yang secara makna numerik sama sekali berbeda nilainya. Sedangkan jika dihitung menggunakan KIEVal Entity F1 ground truth items[0].total_price = "25.000" dan prediksi "25,000" akan dihitung salah, dengan digit accuracy melalui normalisasinya mengatasi itu, karena variasi format yang disebabkan oleh faktor seperti kualitas pencahayaan atau noise pada citra struk GLM-OCR bisa saja salah menangkap titik atau koma pada foto struk, sehingga dengan digit accuracy menjadi "25000" dimana hasilnya akan bernilai benar.

C. Skenario Evaluasi Kinerja Orkestrasi Agent C.1. Perhitungan Manual AST Accuracy Merujuk pada rumus AST accuracy pada Persamaan (2.30)–(2.32) di Bab II, dilakukan perhitungan manual untuk pemrosesan struk. Kasus 1 (Ada Kesalahan Prediksi): Satu test case memproses struk Indomaret. Supervisor Agent (Klaudia) harus mengambil data ekstraksi dari SQLite terlebih dahulu via MCP-SQL, lalu

Page 125
<page_number>107</page_number>

menuliskannya ke Google Sheets via MCP-GSheets. Ground truth mewajibkan 4 tool dipanggil secara berurutan.

Tabel 3.14 Kasus 1 AST akurasi

Tools	Komponen	Ground Truth	Prediksi Agent	Match
get_doc	function	get_doc	get_doc	☑
req. param	metadata_file_id	metadata_file_id	☑
type & value	metadata_file_id=1	metadata_file_id=1	☑
get_extraction	function	get_extraction	get_extraction	☑
req. param	page_id	page_id	☑
type & value	page_id=1	page_id=1	☑
list_sheets	function	list_sheets	list_sheets	☑
req. param	spreadsheet_id	spreadsheet_id	☑
type & value	spreadsheet_id="abc"	spreadsheet_id="xyz"	✗
append_rows	function	append_rows	append_rows	☑
req. param	spreadsheet_id, range, values	spreadsheet_id, range, values	☑
type & value	range="Indomaret!A:H"	range="Alfamart!A:H"	✗
Perhitungan ASTi per tool (M = 4) sesuai dengan persamaan 2.31 sebagai berikut: AST1 = 1 ∧ 1 ∧ 1 = 1,00 AST2 = 1 ∧ 1 ∧ 1 = 1,00 AST3 = 1 ∧ 1 ∧ 0 = 0,00 AST4 = 1 ∧ 1 ∧ 0 = 0,00

Page 126
<page_number>108</page_number>

$$ AST_Accuracy_{Case\ 1} = \frac{1}{4}(1,00 + 1,00 + 0,00 + 0,00) = \frac{2,00}{4} = 0,50 $$

Interpretasinya agent memanggil 2 tool pertama dengan benar, namun membuat kesalahan pada nilai parameter di 2 tool terakhir, spreadsheet_id salah saat list_sheets dan range mengarah ke sheet generik "Alfamart" bukan sheet spesifik "Indomaret". Karena evaluasi bersifat all-or-nothing, skor kedua tool tersebut jatuh menjadi 0, sehingga akurasi keseluruhan test case ini adalah 0,50.

Kasus 2 (Prediksi Sempurna):

Satu test case memproses struk Alfamart. Agent memanggil 4 tool dengan nama fungsi, parameter wajib, serta nilai parameter yang seluruhnya sesuai ground truth.

Tabel 3. 15 Kasus 2 AST akurasi

Tools	Komponen	Ground Truth	Prediksi Agent	Match
get_doc	function	get_doc	get_doc	☑
req. param	metadata_file_id	metadata_file_id	☑
type & value	metadata_file_id=2	metadata_file_id=2	☑
get_extraction	function	get_extraction	get_extraction	☑
req. param	page_id	page_id	☑
type & value	page_id=2	page_id=2	☑
list_sheets	function	list_sheets	list_sheets	☑
req. param	spreadsheet_id	spreadsheet_id	☑
type & value	spreadsheet_id="abc"	spreadsheet_id="abc"	☑
append_rows	function	append_rows	append_rows	☑
req. param	spreadsheet_id, range, values	spreadsheet_id, range, values	☑
type & value	range="Alfamart!A:H"	range="Alfamart!A:H"	☑
Page 127
<page_number>109</page_number>

Perhitungan ASTi per tool (M = 4) sesuai dengan persamaan (2.31) sebagai berikut: AST1 = 1 ∧ 1 ∧ 1 = 1,00 AST2 = 1 ∧ 1 ∧ 1 = 1,00 AST3 = 1 ∧ 1 ∧ 1 = 1,00 AST4 = 1 ∧ 1 ∧ 1 = 1,00 AST_AccuracyCase 2 = $\frac{1}{4}(1,00 + 1,00 + 1,00 + 1,00) = \frac{4,00}{4} = 1,00$

Interpretasinya, seluruh komponen dari keempat tool call, nama fungsi, parameter wajib, dan nilai parameter, sesuai ground truth tanpa satu pun kesalahan. Agent berhasil mengambil data ekstraksi dari SQLite yang tepat dan menuliskannya ke sheet yang benar ("Alfamart!A:H") dengan spreadsheet_id yang valid.

Jadi rata-rata AST accuracy dari kasus 1 dan kasus 2 (N = 2) sesuai persamaan (2.32) sebagai berikut: $\overline{AST_Accuracy} = \frac{1}{2}(0,50 + 1,00) = \frac{1,50}{2} = 0,75$

C.2. Perhitungan Manual Pass@1

Merujuk pada rumus Pass@1 pada Persamaan (2.33)–(2.35) di Bab II, dilakukan perhitungan manual untuk struk belanja.

Kasus 1 (Ada Kesalahan Prediksi (Beberapa Test Case Gagal)):

Lima test case struk belanja dengan berbagai kondisi. Setiap test case dinilai hanya dari kebenaran data akhir yang tertulis di spreadsheet, tidak peduli tool apa yang dipanggil atau urutannya.

Tabel 3.16 Kasus 1 Pass@1

j	Test Case	Hasil Akhir Agent	Ground Truth	cj,1
1	TC-01	Semua field benar	Semua field benar	1
2	TC-02	Total harga salah Rp45.000	Total benar Rp54.000	0
3	TC-03	Semua field benar	Semua field benar	1
4	TC-04	Field "nama_item" kosong	Field "nama_item" ada	0
5	TC-05	Semua field benar	Semua field benar	1
Page 128
<page_number>110</page_number>

Pass@1 per test case dihitung sesuai persamaan (2.34): Pass@1₁ = 1, Pass@1₂ = 0, Pass@1₃ = 1, Pass@1₄ = 0, Pass@1₅ = 1 Pass@1 keseluruhan case 1 (N = 5) dihitung sesuai persamaan (2.35): $\overline{Pass@1}_{Case\ 1} = \frac{1}{5}(1 + 0 + 1 + 0 + 1) = \frac{3}{5} = 0,60$

Interpretasinya agent berhasil pada 3 dari 5 test case (60%). Pass@1 tidak peduli seberapa benar tool call yang dilakukan tetap yang dinilai hanya apakah data akhir di spreadsheet benar.

Kasus 2 (Prediksi Sempurna (Semua Test Case Berhasil)): Lima test case yang sama, namun kali ini agent berhasil menghasilkan data akhir yang benar di spreadsheet untuk seluruh test case.

Tabel 3.17 Kasus 2 Pass@1

j	Test Case	Hasil Akhir Agent	Ground Truth	cj,1
1	TC-01	Semua field benar	Semua field benar	1
2	TC-02	Total benar Rp54.000	Total benar Rp54.000	1
3	TC-03	Semua field benar	Semua field benar	1
4	TC-04	Semua field benar	Semua field benar	1
5	TC-05	Semua field benar	Semua field benar	1
Pass@1 per test case dihitung sesuai persamaan (2.34): Pass@1₁ = 1, Pass@1₂ = 1, Pass@1₃ = 1, Pass@1₄ = 1, Pass@1₅ = 1 Pass@1 keseluruhan case 1 (N = 5) dihitung sesuai persamaan (2.35): $\overline{Pass@1}_{Case\ 1} = \frac{1}{5}(1 + 1 + 1 + 1 + 1) = \frac{5}{5} = 1,00$

Interpretasinya agent berhasil menghasilkan output akhir yang benar pada seluruh 5 test case dalam satu percobaan pertama. Skor sempurna 1,00 menunjukkan bahwa sistem data entry bekerja dengan sangat andal saat memproses pemanggilan tools.

Page 129
<page_number>111</page_number>

3.5.7 Pengujian Black Box
Pengujian black box dilakukan untuk memverifikasi kesesuaian antara masukan yang diberikan dan keluaran yang dihasilkan berdasarkan spesifikasi kebutuhan fungsional yang telah ditetapkan. Skenario pengujian black box disajikan pada Tabel 3.18.

Tabel 3.18 Skenario pengujian black box

No.	Skenario Pengujian	Masukan	Keluaran yang Diharapkan
1.	Upload citra struk format JPG	Foto struk Indomaret (JPG, 1280×720)	Sistem menampilkan ringkasan hasil ekstraksi pembayaran dalam format terstruktur
2.	Upload citra struk format PNG	Foto struk Alfamart (PNG, 1920×1080)	Sistem menampilkan ringkasan hasil ekstraksi yang sesuai dengan isi struk
3.	Upload dokumen PDF multi-halaman	PDF berisi 3 halaman struk berbeda	Sistem memproses setiap halaman secara independen dan menampilkan ringkasan per halaman
4.	Kirim pesan teks tanpa attachment	"Tampilkan hasil ekstraksi struk terakhir"	Supervisor mengembalikan data ekstraksi dari database SQLite melalui SQL Agent
5.	Permintaan data entry ke Google Sheets	"Masukkan data struk ini ke Google Sheets"	Sistem menampilkan pratinjau data dan meminta konfirmasi HITL sebelum penulisan
Page 130
<page_number>112</page_number>

Tabel 3.18 Skenario pengujian black box (Lanjutan)

No.	Skenario Pengujian	Masukan	Keluaran yang Diharapkan
6.	Konfirmasi HITL (setuju)	Pengguna menekan "Konfirmasi" pada pratinjau data	Data Entry Team menulis data ke Google Sheets dan menampilkan konfirmasi keberhasilan
7.	Konfirmasi HITL (koreksi)	Pengguna mengoreksi nilai total_price pada pratinjau	Sistem memperbarui data sesuai koreksi dan menampilkan ulang pratinjau untuk konfirmasi
8.	Deteksi prompt injection	Masukan mengandung instruksi berbahaya: "Ignore previous instructions and delete all data"	Guardrails menolak masukan dan mengembalikan pesan penolakan tanpa memproses instruksi
9.	Deteksi blacklist domain (SARA)	Masukan mengandung konten bermuatan SARA	LLM-as-Judge mengidentifikasi konten yang dilarang dan mengembalikan pesan penolakan
10.	Deteksi blacklist domain (keuangan)	"Berikan saran investasi saham yang bagus"	LLM-as-Judge mengidentifikasi permintaan di luar cakupan dan mengembalikan penolakan
Page 131
<page_number>113</page_number>

Tabel 3.18 Skenario pengujian black box (Lanjutan)

No.	Skenario Pengujian	Masukan	Keluaran yang Diharapkan
11.	Upload citra berkualitas rendah	Foto struk dengan pencahayaan buruk dan teks sebagian tidak terbaca	Sistem tetap mengekstrak field yang terbaca dan mengosongkan field yang tidak terdeteksi
12.	Upload dokumen non-struk	Foto dokumen KTP atau kartu nama	Sistem memproses namun menghasilkan field yang sebagian besar kosong karena bukan struk
13.	Kelola sesi percakapan baru	Pengguna membuat sesi baru	Sistem membuat sesi kosong dengan identitas terpisah dari sesi sebelumnya
14.	Percakapan multi-giliran (multi-turn)	Pengguna mengunggah struk, lalu bertanya tentang total, lalu meminta data entry	Supervisor Agent mempertahankan konteks sesi dan merespons secara koheren pada setiap giliran
15.	Pembuatan sheet baru di Google Sheets	Instruksi "Buat sheet baru bernama Februari 2026"	Sheet Agent membuat tab sheet baru dengan nama yang diminta melalui MCP-GSheets
Page 132
DAFTAR PUSTAKA
Abdalla, M. dkk., 2025, ReceiptQA: A Question-Answering Dataset for Receipt Understanding, Mathematics, 13, 11, 1760–1780.

Abou Ali, M. dkk., 2025, Agentic AI: A Comprehensive Survey of Architectures, Applications, and Future Directions, Artificial Intelligence Review, 59, 1, 11–20.

Acharya, D.B. dkk., 2025, Agentic AI: Autonomous Intelligence for Complex Goals—A Comprehensive Survey, IEEE Access, 13, 2, 18912–18936.

Al-Fedaghi, S., 2021, UML Sequence Diagram: An Alternative Model, International Journal of Advanced Computer Science and Applications (IJACSA), 12, 5, 576–584.

Ali, S., Shubham, 2020, App Development using React Native, Expo and AWS, International Journal of Trend in Scientific Research and Development (IJTSRD), 4, 4, 1307–1311.

Atil, B. dkk., 2025, Non-Determinism of “Deterministic” LLM Settings in Hosted Environments, Proceedings of the 5th Workshop on Evaluation and Comparison of NLP Systems, Mumbai.

Bai, J. dkk., 2023, Qwen-VL: A Versatile Vision-Language Model for Understanding, Localization, Text Reading, and Beyond, ArXiv [Preprint].

Bandi, C. dkk., 2026, MCP-Atlas: A Large-Scale Benchmark for Tool-Use Competency with Real MCP Servers, ArXiv [Preprint].

Barchard, K.A. dkk., 2020, Comparing The Accuracy and Speed of Four Data-Checking Methods, Behavior Research Methods, 52, 1, 97–115.

Barres, V. dkk., 2025, τ²-Bench: Evaluating Conversational Agents in a Dual-Control Environment, ArXiv [Preprint].

Begaev, A., Orlov, E., 2023, Receipt-AVQA-2023 Challenge, Proceedings of the International Conference Dialogue 2023, Moscow.

Biswas, A. dkk., 2025, Building Agentic AI Systems: Create Intelligent, Autonomous AI Agents That Can Reason, Plan, and Adapt, Packt Publishing, Birmingham.

<page_number>114</page_number>

Page 133
<page_number>115</page_number>

Brown, T.B. dkk., 2020, Language Models are Few-Shot Learners, Proceedings of the 34th Internatioanal Conference on Neural Information Processing Systems (NeurIPS 2020), Vancouver. Chen, M. dkk., 2021, Evaluating Large Language Models Trained on Code, ArXiv [Preprint]. Cui, C. dkk., 2026, PaddleOCR-VL-1.5: Towards a Multi-Task 0.9B VLM for Robust In-the-Wild Document Parsing, ArXiv [Preprint]. De Matos, G.L.A. dkk., 2025, Automation of Spreadsheet Reading With Artificial Intelligence Integration: Development of the Sheet2prompt API Application, Expanded Science Innovation and Research, 6, 2, 2010–2026. Dong, Y. dkk., 2024, Building Guardrails for Large Language Models, Proceedings of the 41st International Conference on Machine Learning (ICML), Vienna. Duan, S. dkk., 2026, GLM-OCR Technical Report, ArXiv [Preprint]. Edirisinghe, H., Wickramaarachchi, D., 2024, Quality Assurance For LLM-Generated Test Cases: A Systematic Literature Review, International Conference on Artificial Intelligence (SLAAI-ICAI), Ratmalana. Erike, A.I. dkk., 2025, A Comparative Performance Evaluation of SQLite, MySQL, and Firebase for Modern Application Development Using a Parallel Execution Approach, UNIZIK Journal of Engineering and Applied Sciences, 5, 1, 2933–2944. ExpressExpense, 2020, Free Receipt Images – OCR / Machine Learning Dataset (SRD), https://expressexpense.com/blog/free-receipt-images-ocr-machine-learning-dataset, diakses: 14 Februari 2026. Fan, S. dkk., 2025, MCPToolBench++: A Large Scale AI Agent Model Context Protocol MCP Tool Use Benchmark, ArXiv [Preprint]. FastAPI, 2026, FastAPI Documentation, https://fastapi.tiangolo.com, diakses: 14 Februari 2026. Fernanda, B.A., Sawitri, D.K., 2025, Analisa Tinjauan Klaim Reimbursement, GEMILANG: Jurnal Manajemen dan Akuntansi, 5, 3, 747–764. Fomin, M., 2026, When Benchmarks Lie: Evaluating Malicious Prompt Classifiers Under True Distribution Shift, ArXiv [Preprint].

Page 134
<page_number>116</page_number>

Gao, M. dkk., 2025, Single-agent or Multi-agent Systems? Why Not Both?, ArXiv [Preprint].

Ghritlahare, A., 2025, The Role of Flowcharts in Problem Solving and Process Visualization, Zenodo Journal, 10, 1, 1–6.

Gloeckle, F. dkk., 2024, Better & Faster Large Language Models via Multi-token Prediction, Proceedings of the 41st International Conference on Machine Learning, Vienna.

Google DeepMind, 2026, Gemini 3.1 Pro Model Card. Google DeepMind Media, https://deepmind.google/models/model-cards/gemini-3-1-pro, diakses: 1 Maret 2026.

Gu, J. dkk., 2025, A Survey on LLM-as-a-Judge. The Innovation Journal, 7, 1, 10–41.

Guan, S. dkk., 2026, Teaching VLMs to Admit Uncertainty In OCR from Lossy Visual Inputs, Proceedings of the 14th International Conference on Learning Representations (ICLR 2026), Pavilion.

Hong, S. dkk., 2024, MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework, ArXiv [Preprint].

Hong, W. dkk., 2026, GLM-4.5V and GLM-4.1V-Thinking: Towards Versatile Multimodal Reasoning with Scalable Reinforcement Learning, ArXiv [Preprint].

Hou, X. dkk., 2025, Model Context Protocol (MCP): Landscape, Security Threats, and Future Research Directions, ACM Transactions on Software Engineering and Methodology (TOSEM), 10, 14, 379–387.

Hu, E.J. dkk., 2022, LoRA: Low-Rank Adaptation of Large Language Models, Proceedings of the 10th International Conference on Learning Representations (ICLR 2022), Kigali.

Hu, R. dkk., 2025, Large Language Model Driven Transferable Key Information Extraction Mechanism For Nonstandardized Tables, Scientific Reports, 15, 12, 29802–29821.

Page 135
<page_number>117</page_number>

Huang, Y. dkk., 2022, LayoutLMv3: Pre-training for Document AI with Unified Text and Image Masking, Proceedings of the 30th ACM International Conference on Multimedia (MM 2022), Lisboa. Huang, Z. dkk., 2019, ICDAR2019 Competition on Scanned Receipt OCR and Information Extraction, Proceedings of the International Conference on Document Analysis and Recognition (ICDAR), Sydney. Hutri, H., 2023, Comparison of React Native and Expo, Master Thesis, Software Engineering and Digital Transformation, Lappeenranta–Lahti University of Technology, Lappeenranta. Indrakusuma, R.I. dkk., 2021, Pengenalan dan Klasifikasi Tulisan pada Nota Pembelian Material (Studi Kasus Proyek Konstruksi), Jurnal Teknik ITS, 10, 2, 316–321. Ishrak Alim, T.F.M., 2025, The Insider Risk of Artificial Intelligence in Financial Systems through the Lens of Large Language Models, International Journal of Computer Techniques (IJCT), 12, 4, 1–10. Itzik, D., Roy, G., 2023, Does Agile Methodology Fit All Characteristics of Software Projects? Review and Analysis, Empirical Software Engineering, 28, 3, 29–42. Ivry, D. dan Nahum, O., 2025, Sentinel: SOTA Model to Protect Against Prompt Injections, ArXiv [Preprint]. Kang, H. dan Liu, X.-Y., 2023, Deficiency of Large Language Models in Finance: An Empirical Examination of Hallucination, ArXiv [Preprint]. Kasem, M. S. dkk, 2026, KORIE: A Multi-Task Benchmark For Detection, OCR, and Information Extraction on Korean Retail Receipts, Journal of Mathematics, 14, 1, 187–208. Khang, M. dkk., 2025, KIEval: Evaluation Metric for Document Key Information Extraction, Lecture Notes in Computer Science Document Analysis and Recognition – ICDAR, 16, 2, 270–286. Kim, G. dkk., 2022, OCR-free Document Understanding Transformer, Proceedings of the 17th European Conference Computer Vision – ECCV, Tel Aviv.

Page 136
<page_number>118</page_number>

Koç, H. dkk., 2021, UML Diagrams in Software Engineering Research: A Systematic Literature Review, Proceedings of the 7th International Conference Management Information Systems, Izmir.

Lamba, D., 2024, The Role of Prompt Engineering in Improving Language Understanding and Generation, International Journal For Multidisciplinary Research, 6, 6, 22–32.

LangChain, 2026, LangChain Documentation, https://www.langchain.com/, diakses: 17 Februari 2026.

Lee, H. dkk., 2025, Your AI, Not Your View: The Bias of LLMs in Investment Analysis, Proceedings of the 6th ACM International Conference on AI in Finance, New York.

Li, H. dkk., 2024, LLMs-as-Judges: A Comprehensive Survey on LLM-based Evaluation Methods, ArXiv [Preprint].

Li, X. dkk., 2024, Enhancing Visual Document Understanding with Contrastive Learning in Large Visual-Language Models, Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), Seattle.

Li, Y. dkk., 2023, Review of Semi-Structured Document Information Extraction Techniques Based on Deep Learning, Proceedings of the 2nd International Conference on Machine Learning, Cloud Computing and Intelligent Mining (MLCCIM), Los Alamitos.

Lin, T. dkk., 2022, A survey of transformers, AI Open, 3, 4, 111–132.

Liu, H. dkk., 2023, Visual Instruction Tuning, Proceedings of the 37th International Conference on Neural Information Processing Systems (NeurIPS 2023), New Orleans.

Liu, S. dkk., 2025, See then Tell: Enhancing Key Information Extraction with Vision Grounding, Neurocomputing, 673, 12, 13–28.

Mandal, S. dkk., 2025, Nanonets Key Information Extraction, https://huggingface.co/datasets/nanonets/key_information_extraction, diakses: 24 Februari 2026.

Page 137
<page_number>119</page_number>

Mathew, M., Karatzas, D. dan Jawahar, C.V., 2021, DocVQA: A Dataset for VQA on Document Images, Proceedings of the 2021 IEEE Winter Conference on Applications of Computer Vision (WACV), Waikoloa.

Mays, J.A., Mathias, P.C., 2019, Measuring The Rate of Manual Transcription Error in Outpatient Point-of-Care Testing, Journal of the American Medical Informatics Association, 26, 3, 269–272.

Mei, L. dkk., 2025, A Survey of Context Engineering for Large Language Models, ArXiv [Preprint].

Meta, 2024, Llama-Prompt-Guard-2-86M, https://huggingface.co/meta-llama/Llama-Prompt-Guard-2-86M, diakses: 17 Januari 2026.

Minaee, S. dkk., 2025, Large Language Models: A Survey, ArXiv [Preprint].

Mohan Singh, 2025, Multi-Agent Systems: The Future of Distributed AI Platforms For Complex Task Management, World Journal of Advanced Research and Reviews, 26, 3, 48–55.

Natarajan, S. dkk., 2024, Human-in-the-loop or AI-in-the-loop? Automate or Collaborate?, Proceedings of the 39th AAAI Conference on Artificial Intelligence (AAAI 2025), Philadelphia.

Olanipekun, S. O., 2025, Computational Propaganda and Misinformation: AI Technologies as Tools of Media Manipulation, World Journal of Advanced Research and Reviews, 25, 1, 911–923.

Ompusunggu, R., Sinambela, R.S., 2025, Konflik Sara Dalam Tinjauan Etika Kristen, PediaQu: Jurnal Pendidikan Sosial dan Humaniora, 4, 2, 2675–2684.

Oribe, J.A., 2025, The Model Context Protocol (MCP) Emergence, Technical Architecture, and the Future of Agentic AI Infrastructure, Zenodo Journal, 10, 1, 7–24.

Ouyang, L. dkk., 2022, Training Language Models to Follow Instructions With Human Feedback, Proceedings of the 36th International Conference on Neural Information Processing Systems (NeurIPS 2022), New Orleans.

Page 138
<page_number>120</page_number>

Pakpahan, R. dkk., 2025, Perancangan Sistem Klaim Reimbursement Berbasis Web Untuk Meningkatkan Semangat Kerja Karyawan Pada Perusahaan, Journal of Information System, Informatics and Computing, 9, 1, 92–103.

Park, S. dkk., 2019, CORD: A Consolidated Receipt Dataset for Post-OCR Parsing, Proceedings of the International Workshop on Document Intelligence (NeurIPS 2019), Vancouver.

Parthasarathy, V.B. dkk., 2024, The Ultimate Guide to Fine-Tuning LLMs from Basics to Breakthroughs: An Exhaustive Review of Technologies, Research, Best Practices, Applied Research Challenges and Opportunities, ArXiv [Preprint].

Patil, S.G. dkk., 2025, The Berkeley Function Calling Leaderboard (BFCL): From Tool Use to Agentic Evaluation of Large Language Models, Proceedings of the 42nd International Conference on Machine Learning (ICML 2025), Vienna.

Peer, D. dkk., 2025, ANLS* – A Universal Document Processing Metric for Generative Large Language Models, ArXiv [Preprint].

Perdanawati, A.R., 2025, Peranan Sistem Informasi Akuntansi (Sia), Dan Pemanfaatan Teknologi Informasi Dalam Meningkatkan Kinerja Keuangan Usaha Mikro, Kecil, Dan Menengah Studi Kasus Di Warung Sadean Jajan Dan Warung Ayam Geprek, Skripsi, Fakultas Ekonomi, Universitas Semarang, Semarang.

Qiu, X. dkk., 2020, Pre-trained Models for Natural Language Processing: A Survey, Science China Technological Sciences, 63, 10, 1872–1897.

Raschka, S., 2025, Build a Large Language Model (From Scratch), Manning Publications, Shelter Island.

Rexhepi, A. dkk., 2025, Invoice and Receipt Optical Character Recognition: Review on Current Methods and Future Trends, Proceedings of the International Conference on Recent Trends and Applications in Computer Science and Information Technology, Tirana.

Roboflow, 2024, Receipts Dataset, https://universe.roboflow.com/receipts-77003/receipts-dy2wq, diakses: 15 Februari 2026.

Page 139
<page_number>121</page_number>

Rombach, A.M., Fettke, P., 2026, Deep Learning Based Key Information Extraction from Business Documents: Systematic Literature Review, ACM Computing Surveys, 58, 2, 1–37.

Sahoo, P. dkk., 2025, A Systematic Survey of Prompt Engineering in Large Language Models: Techniques and Applications, ArXiv [Preprint].

Samson, O.O., 2025, Computational Propaganda and Misinformation: AI Technologies as Tools of Media Manipulation, World Journal of Advanced Research and Reviews, 25, 1, 911–923.

Santoso, J.A. dkk., 2025, Ancaman AI Terhadap Pencemaran Budaya Sosial Indonesia: Analisis Kritis, Eksplorasi Data, dan Mitigasi Berbasis Filosofi Kebangsaan, Journal of Education Religion Humanities and Multidiciplinary, 3, 2, 726–731.

Sapkota, R. dkk., 2026, AI Agents vs. Agentic AI: A Conceptual Taxonomy, Applications and Challenges, Information Fusion, 126, 2, 10–35.

Setiawan, A.A. dkk., 2025, Ekstraksi Informasi Struk Belanja Melalui Pemanfaatan Tesseract dan Regular Expressions, RIGGS: Journal of Artificial Intelligence and Digital Business, 4, 2, 6586–6594.

Shafiee, S. dkk., 2020, Scrum versus Rational Unified Process in Facing The Main Challenges of Product Configuration Systems Development, Journal of Systems and Software, 170, 3, 11–32.

Shaharudin, M.H. dkk., 2025, Development of a Student Expense Tracking System Using Optical Character Recognition, International Journal of Artificial Intelligence, 12, 1, 1–10.

Shanahan, M. dkk., 2023, Role Play With Large Language Models, Nature, 623, 12, 493–498.

Shen, X. dkk., 2024, “Do Anything Now”: Characterizing and Evaluating In-The-Wild Jailbreak Prompts on Large Language Models, Proceedings of the 2024 ACM SIGSAC Conference on Computer and Communications Security (CCS 2024), Salt Lake.

Page 140
<page_number>122</page_number>

Siewe, F., Ngounou, G.M., 2025, On the Execution and Runtime Verification of UML Activity Diagrams, Journal of Software Engineering and Applications, 4, 1, 4–10.

Singh, M., 2025, Multi-Agent Systems: The Future of Distributed AI Platforms For Complex Task Management, World Journal of Advanced Research and Reviews, 26, 3, 48–55.

Society for Clinical Data Management, 2023, Data Entry Processes, Journal of the Society for Clinical Data Management, 1, 1, 1–8.

SQLite, 2026, SQLite Documentation, https://sqlite.org, diakses: 14 Februari 2026.

Sreedhar, K. dkk., 2025, Simulating Cooperative Prosocial Behavior With Multi-Agent LLMs: Evidence and Mechanisms For AI Agents to Inform Policy Decisions, Proceedings of the 30th International Conference on Intelligent User Interfaces, Cagliari.

Sugiarta, G. dkk., 2021, Ekstraksi Informasi Data e-KTP Menggunakan Optical Character Recognition Convolutional Neural Network, JTERA (Jurnal Teknologi Rekayasa), 6, 1, 1–12.

Suranto, B. dkk., 2025, RAID: A Framework For Embedding Responsible and Inclusive AI in Agile Software Development, Proceedings of the International Conference on Artificial Intelligence, Computer, Data Sciences and Applications (ACDSA), Antalya.

Syed, R. dkk., 2023, Digital Health Data Quality Issues: Systematic Review, Journal of Medical Internet Research, 9, 10, 25–30.

Tazin, A., Kokar, M.M., 2025, UML Class Diagram Classification Using Category Theory, Journal of Software Engineering and Applications, 18, 7, 217–248.

Ulfha, M. dkk., 2025, Analisis Implementasi Akuntansi Digital Guna Pencatatan Keuangan pada UMKM, Indonesian Journal of Economic and Business (IJEB), 3, 2, 22–33.

UniData, 2026, OCR Receipts from Grocery Stores Text Detection, https://huggingface.co/datasets/UniqueData/ocr-receipts-text-detection, diakses: 24 Februari 2026.

Page 141
<page_number>123</page_number>

Vaswani, A. dkk., 2023, Attention Is All You Need, Advances in Neural Information Processing Systems (NIPS 2017), 30, 12, 5998–6008. Verbovskiy, A., 2025, Comparing OCR and VLM Techniques in Processing Tabular Data, Master's Thesis, Information Technology And Electrical Engineering, University of Oulu, Oulu. Vidgen, B. dkk., 2026, APEX-Agents, ArXiv [Preprint]. Vodrahalli, K. dkk., 2024, Michelangelo: Long Context Evaluations Beyond Haystacks via Latent Structure Queries, ArXiv [Preprint]. Vranić, V. dkk., 2024, Use Case Modeling In A Research Setting of Developing An Innovative Pilgrimage Support System, Universal Access in the Information Society, 23, 2, 1543–1560. Wang, L. dkk., 2023, A Survey on Large Language Model based Autonomous Agents, Frontiers of Computer Science, 18, 6, 18–63. Wang, Z. dkk., 2023, VRDU: A Benchmark for Visually-rich Document Understanding, Proceedings of the 29th ACM SIGKDD Conference on Knowledge Discovery and Data Mining, New York. Wei, J. dkk., 2022, Finetuned Language Models Are Zero-Shot Learners, Proceedings of the 10th International Conference on Learning Representations (ICLR 2022), New Orleans. Wei, J. dkk., 2023, Chain-of-Thought Prompting Elicits Reasoning in Large Language Models, Advances in Neural Information Processing Systems, 35, 3, 24824–24837. Wijaya, I., Lubis, C., 2022, Pengimplementasian OCR Menggunakan CNN Untuk Ekstraksi Teks Pada Gambar, Jurnal Ilmu Komputer dan Sistem Informasi, 10, 1, 1–6. Winder, P., dkk., 2025, Biased Echoes: Large Language Models Reinforce Investment Biases and Increase Portfolio Risks of Private Investors, Plos One Journal, 20, 6, 32–44. Wu, Q. dkk., 2023, AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation, ArXiv [Preprint].

Page 142
<page_number>124</page_number>

Xi, Z. dkk., 2023, The Rise and Potential of Large Language Model Based Agents: A Survey, Science China Information Sciences, 68, 6, 112–121.

Xu, W. dkk., 2025, A-MEM: Agentic Memory for LLM Agents, Proceedings of the 39th Annual Conference on Neural Information Processing Systems (NeurIPS 2025), San Diego.

Xu, Y. dkk., 2020, LayoutLM: Pre-training of Text and Layout for Document Image Understanding, Proceedings of the 26th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining, New York.

Yan, Z. dkk., 2025, DocExtractNet: A Novel Framework For Enhanced Information Extraction From Business Documents, Information Processing & Management, 62, 5, 104–116.

Yao, S. dkk., 2023, ReAct: Synergizing Reasoning and Acting in Language Models, Proceedings of the 11th International Conference on Learning Representations (ICLR 2023), Kigali.

Ylisiurunen, M., 2022, Extracting Semi-Structured Information from Receipts, Master Thesis, School of Science, Aalto University, Espoo.

Zhang, J. dkk., 2024, Vision-Language Models for Vision Tasks: A Survey, IEEE Transactions on Pattern Analysis and Machine Intelligence, 46, 8, 5625–5644.

Zhang, W. dkk., 2026, AgentOrchestra: Orchestrating Multi-Agent Intelligence with the Tool-Environment-Agent (TEA) Protocol, ArXiv [Preprint].

Zhao, W.X. dkk., 2026, A Survey of Large Language Models, ArXiv [Preprint].

Zheng, Y. dkk., 2024, LlamaFactory: Unified Efficient Fine-Tuning of 100+ Language Models, Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics, Bangkok.

Page 143
