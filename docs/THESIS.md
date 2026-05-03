Page 1
SEMINAR PROPOSAL

OTOMATISASI DATA ENTRY STRUK PEMBELIAN MENGGUNAKAN VISION LANGUAGE MODEL FINE-TUNED DENGAN LORA DAN ORKESTRASI HIERARCHICAL MULTI-AGENT BERBASIS MODEL CONTEXT PROTOCOL (MCP)

Diajukan Untuk Memenuhi Salah Satu Syarat Memperoleh Gelar Sarjana Teknik

<img>Universitas Halu Oleo Logo</img>

LA ODE MUHAMMAD YUDHY PRAYITNO E1E122064

JURUSAN INFORMATIKA FAKULTAS TEKNIK UNIVERSITAS HALU OLEO KENDARI 2025

Page 2
LEMBAR PENGESAHAN

SEMINAR PROPOSAL

OTOMATISASI DATA ENTRY STRUK PEMBELIAN MENGGUNAKAN VISION LANGUAGE MODEL FINE-TUNED DENGAN LORA DAN ORKESTRASI HIERARCHICAL MULTI-AGENT BERBASIS MODEL CONTEXT PROTOCOL (MCP)

Adalah benar dibuat oleh saya sendiri dan belum pernah dibuat dan diserahkan sebelumnya baik sebagian ataupun seluruhnya, baik oleh saya maupun orang lain, baik di Universitas Halu Oleo ataupun institusi pendidikan lainnya.

Kendari, 2025

<signature>La Ode Muhammad Yudhy Prayitno</signature> E1E122064

Pembimbing I Prof. Dr. Ir. La Ode Muhammad Golok Jaya, ST., MT. NIP. 197610202005011002

Pembimbing II Asa Hari Wibowo, S.T., M.Eng. NIP. 199408172022031014

Mengetahui, Ketua Jurusan Informatika Fakultas Teknik Universitas Halu Oleo

<signature>Isnawaty, S.Si., M.T.</signature> NIP. 197611172008122001

<page_number>ii</page_number>

Page 3
iii

Page 4
BAB I
PENDAHULUAN
1.1 Latar Belakang
Proses data entry (entri data) secara manual merupakan salah satu aktivitas operasional yang paling rentan terhadap kesalahan dalam dunia bisnis. Tingkat kesalahan pada entri data manual secara konsisten berkisar antara 1% hingga 4% per field, dan dapat mencapai 26,9% pada kondisi tertentu akibat faktor kelelahan serta distraksi operator manusia (Mays dan Mathias, 2019; Barchard dkk., 2020). Penelitian empiris menunjukkan bahwa metode verifikasi visual (visual checking) menghasilkan risiko kesalahan yang jauh lebih tinggi dibandingkan pendekatan otomatis. Kesalahan tersebut, meskipun tampak kecil pada skala individual, dapat mengakibatkan ketidakakuratan yang signifikan dalam laporan keuangan apabila tidak terdeteksi dan terkoreksi lebih awal. Dalam konteks pencatatan transaksi berbasis struk pembelian, permasalahan ini diperburuk oleh variasi format struk yang sangat beragam antar merchant, tipografi yang tidak konsisten, serta kualitas cetakan yang sering kali kurang optimal. Kondisi ini menjadikan entri data dari struk pembelian sebagai salah satu kasus data entry yang paling menantang untuk diotomatisasi secara akurat.

Permasalahan entri data manual memiliki relevansi yang tinggi dalam konteks Indonesia, baik pada tingkat individu maupun organisasi. Dalam pengelolaan keuangan pribadi, banyak masyarakat masih mengandalkan pencatatan pengeluaran secara tradisional, seperti menyimpan dan mencatat struk belanja pada kertas, buku catatan, atau dompet secara tidak terstruktur. Praktik ini sering kali tidak dilakukan secara rutin karena keterbatasan waktu, aktivitas yang padat, serta rendahnya kebiasaan pencatatan keuangan, sehingga detail transaksi mudah terlupakan atau tidak tercatat secara lengkap (Shaharudin dkk., 2025). Kondisi serupa juga terjadi pada sektor Usaha Mikro, Kecil, dan Menengah (UMKM), di mana sebagian pelaku usaha masih mencatat transaksi pembelian maupun pengeluaran usaha secara manual pada buku kas sederhana. Metode ini tidak hanya memerlukan waktu lebih lama, tetapi juga meningkatkan risiko kesalahan

<page_number>1</page_number>

Page 5
<page_number>2</page_number>

pencatatan, salah perhitungan, serta kehilangan bukti transaksi seperti struk atau nota pembelian (Perdanawati, 2025; Ulfha dkk., 2025). Selain itu, dalam lingkungan perusahaan, struk pembelian sering kali menjadi dokumen penting dalam proses klaim reimbursement karyawan. Proses yang masih bergantung pada pengumpulan bukti fisik dan entri data manual berpotensi menimbulkan berbagai kendala, seperti kehilangan dokumen, kesalahan input nominal atau tanggal, serta keterlambatan verifikasi oleh bagian keuangan (Fernanda dan Sawitri, 2025; Pakpahan, Fitriyani dan Kholik, 2025). Berbagai kondisi tersebut menunjukkan bahwa pencatatan transaksi berbasis struk pembelian masih menghadapi tantangan signifikan dalam hal efisiensi, akurasi, dan konsistensi pencatatan data, sehingga memerlukan solusi otomatisasi yang mampu mendukung transformasi pencatatan keuangan menuju sistem yang lebih digital dan terintegrasi.

Pendekatan otomatisasi tradisional menggunakan Optical Character Recognition (OCR) telah lama diterapkan untuk mengekstrak teks dari dokumen, namun memiliki keterbatasan yang signifikan. Penelitian oleh Indrakusuma et al. (2021) menunjukkan bahwa sistem OCR berbasis Tesseract yang dikombinasikan dengan Support Vector Machine memerlukan waktu pemrosesan rata-rata 8,89 detik per dokumen dan pada setiap proses pemindaian masih menghasilkan sekitar 1–2 kesalahan pembacaan maupun klasifikasi (Indrakusuma, Ahmadiyah dan Ariyani, 2021). Pendekatan serupa yang mengandalkan Tesseract dan Regular Expressions masih bergantung pada aturan tetap (rule-based parsing) untuk mengekstrak informasi dari struk. Ketergantungan pada pola yang telah ditentukan membuat metode ini kurang adaptif terhadap variasi format struk serta rentan menghasilkan ekstraksi yang tidak akurat ketika kualitas gambar buruk atau struktur struk berbeda dari pola yang telah didefinisikan (Setiawan, Guntara dan Purwaamijaya, 2025). Implementasi OCR berbasis Convolutional Neural Network (CNN) untuk ekstraksi teks gambar menghasilkan F1-score 49,18% pada deteksi dan Correctly Recognized Word 55,80% pada pengenalan (Wijaya dan Lubis, 2022). Demikian pula, OCR CNN untuk data e-KTP mencapai error rate 5% dalam 30 detik, namun membutuhkan koreksi manual pada field yang terpotong akibat kualitas citra yang bervariasi (Sugiarta, Andini dan Hidayatullah, 2021). Keterbatasan mendasar OCR

Page 6
<page_number>3</page_number>

tradisional terletak pada ketidakmampuannya memahami struktur semantik dokumen, OCR hanya menghasilkan teks mentah tanpa informasi tentang makna atau hubungan semantik antar elemen teks.

Bidang pemahaman dokumen telah mengalami pergesan paradigma dari OCR tradisional menuju Vision Language Model (VLM) yang mampu memproses dokumen secara end-to-end. Kim dkk., 2022 memperkenalkan Donut, sebuah OCR-free Document Understanding Transformer yang memetakan citra dokumen langsung ke token JSON terstruktur tanpa memerlukan tahapan OCR terpisah, dan mencapai hasil state-of-the-art pada benchmark CORD dan DocVQA. Perkembangan selanjutnya menghasilkan VLM skala kecil seperti GLM-OCR dengan hanya 0,9 miliar parameter, yang mencapai skor 94,62 pada OmniDocBench V1.5 serta 94,5% pada skenario Receipt Key Information Extraction (KIE) dunia nyata (Z.ai, 2026). Tinjauan sistematis oleh Rombach & Fettke, 2026 terhadap 130 pendekatan KIE berbasis deep learning pada dokumen bisnis menunjukkan bahwa metode berbasis LLM pertama kali muncul dalam penelitian KIE pada tahun 2023 dan menjadi kategori kedua terbanyak pada tahun 2024, mengonfirmasi transisi cepat dari pendekatan konvensional ke pendekatan berbasis model bahasa. Kemampuan VLM dalam memahami konteks visual dokumen secara holistik, termasuk hubungan spasial dan semantik antar elemen, menjadikannya solusi yang lebih tepat untuk tugas KIE dari dokumen semi-structured seperti struk pembelian dibandingkan dengan pendekatan berbasis aturan atau OCR tradisional.

Meskipun VLM telah menunjukkan kemampuan ekstraksi informasi yang tinggi, proses otomatisasi data entry tidak berhenti pada tahap ekstraksi. Data yang telah diekstrak perlu diteruskan ke database, spreadsheet, atau sistem pencatatan lainnya secara aman dan tervalidasi. Kebutuhan ini memerlukan sistem orkestrasi yang mampu mengoordinasikan berbagai komponen secara otonom. Paradigma Agentic AI, yang mengacu pada sistem kecerdasan buatan otonom dengan kemampuan adaptasi, pengambilan keputusan tingkat lanjut, dan kemandirian operasional Abou Ali dkk., 2025, menawarkan kerangka kerja yang tepat untuk kebutuhan tersebut. Pengembangan sistem agentic selanjutnya didukung oleh

Page 7
<page_number>4</page_number>

inovasi arsitektur seperti Model Context Protocol (MCP) yang diperkenalkan oleh Anthropic pada November 2024 sebagai standar terbuka untuk integrasi agent-tool (Hou dkk., 2025). MCP menggunakan arsitektur client-server berbasis JSON-RPC 2.0, dan pada Desember 2025 telah didonasikan kepada Agentic AI Foundation di bawah Linux Foundation dengan dukungan dari OpenAI, Google, dan Microsoft. Adopsi masif ini, yang ditunjukkan oleh lebih dari 97 juta unduhan SDK bulanan dan 5.800 lebih MCP server dalam produksi, mengonfirmasi MCP sebagai protokol standar industri untuk membangun sistem agent yang aman dan terinteroperabilitas (Anthropic, 2025).

Berdasarkan tinjauan terhadap literatur yang ada, ditemukan bahwa penelitian-penelitian sebelumnya dalam domain KIE struk pembelian hanya berfokus pada tahap ekstraksi informasi tanpa menangani alur hilir berupa entri data otomatis ke sistem pencatatan. Framework multi-agent seperti MetaGPT (Hong dkk., 2024) dan AutoGen (Wu dkk., 2023) mendemonstrasikan pola kolaborasi yang kuat namun menggunakan integrasi tool secara ad-hoc. Belum terdapat penelitian akademis yang menggabungkan VLM ter-fine-tune berskala kecil untuk KIE struk pembelian dengan orkestrasi hierarchical multi-agent berbasis MCP dalam satu pipeline end-to-end. Selain itu, evaluasi pada penelitian sebelumnya umumnya mengukur kualitas ekstraksi atau kinerja agent secara terpisah, bukan keduanya dalam satu sistem terintegrasi.

Berdasarkan latar belakang serta kesenjangan penelitian yang telah diuraikan, diusulkan penelitian dengan judul "Otomatisasi Data Entry Struk Pembelian menggunakan Vision Language Model Fine-Tuned dengan LoRA dan Orkestrasi Hierarchical Multi-Agent berbasis Model Context Protocol (MCP)". Penelitian ini mengembangkan sistem bernama Klaudia yang menggunakan GLM-OCR 0,9B yang di-fine-tune dengan Low-Rank Adaptation (LoRA) melalui LLaMA Factory untuk ekstraksi informasi kunci dari struk pembelian, diorkestrasi melalui arsitektur Hierarchical Agent Teams menggunakan LangGraph dengan MCP-SQLite dan MCP-GSheets sebagai batas eksekusi tool, dilindungi oleh guardrails ganda (Llama Prompt Guard 2 dan LLM-as-Judge), serta dilengkapi mekanisme Human-in-the-Loop (HITL) sebelum operasi penulisan data.

Page 8
<page_number>5</page_number>

Kinerja sistem dievaluasi secara komprehensif menggunakan metrik ekstraksi (KIEval dan ANLS*) serta metrik agentic (AST accuracy dan Pass@K).

1.2 Rumusan Masalah
Berdasarkan latar belakang yang telah diuraikan sebelumnya, rumusan masalah dalam penelitian ini adalah sebagai berikut:

Bagaimana merancang model yang mampu mengekstrak informasi kunci (key information extraction) dari foto struk pembelian berbasis semantik dengan GLM-OCR 0.9B?
Bagaimana membangun sistem yang mampu secara otomatis melakukan entri data ke dalam sistem pencacatan digital berupa spreadsheet tanpa memerlukan pengetikan ulang secara manual dengan arsitektur Hierarchical Multi-Agent berbasis MCP?
1.3 Batasan Masalah
Adapun batasan masalah yang ditetapkan peneliti agar pembahasan dari penulisan ini tidak melenceng jauh dari topik utama yaitu sebagai berikut:

Dokumen yang diproses terbatas hanya pada hasil cetakan struk pembelian dalam format foto (JPG, PNG) atau PDF.
Sistem hanya melakukan pengenalan dan pencatatan data ke Google Sheets sebagai media spreadsheet tujuan, tidak mencakup integrasi dengan aplikasi akuntansi atau sistem pencatatan keuangan lainnya.
Antarmuka sistem diimplementasikan pada platform mobile iOS dan tidak mencakup pengembangan versi Android atau web secara penuh pada tahap penelitian ini.
1.4 Tujuan Penelitian
Adapun tujuan dari penelitian ini adalah sebagai berikut:

Merancang model berbasis kecerdasan buatan yang mampu mengekstrak informasi kunci (key information extraction) dari foto struk pembelian berbasis semantik dengan GLM-OCR 0.9B.
Page 9
<page_number>6</page_number>

Membangun sistem berbasis kecerdasan buatan yang mampu secara otomatis memasukkan data hasil pengenalan ke dalam Google Sheets tanpa memerlukan pengetikan ulang secara manual oleh pengguna dengan arsitektur Hierarchical Multi-Agent berbasis MCP.
1.5 Manfaat Penelitian
Adapun manfaat dari penelitian ini adalah sebagai berikut:

Memberikan solusi otomatisasi pencatatan transaksi dari struk pembelian yang dapat mengurangi kesalahan entri data manual dan mempercepat proses pencatatan keuangan.
Memberikan kontribusi ilmiah berupa arsitektur sistem yang mengintegrasikan pengenalan dokumen berbasis kecerdasan buatan dengan pencatatan data otomatis, yang dapat menjadi referensi bagi penelitian selanjutnya di bidang otomatisasi pemrosesan dokumen keuangan.
1.6 Sistematika Penulisan Laporan
Adapun sistematika penulisan yang digunakan dalam penyusunan penelitian ini adalah sebagai berikut:

BAB I PENDAHULUAN

Bab ini memuat latar belakang permasalahan entri data manual dan kebutuhan otomatisasi berbasis Agentic AI, rumusan masalah, batasan masalah, tujuan penelitian, manfaat penelitian, sistematika penulisan, serta tinjauan pustaka yang mengkaji penelitian terdahulu terkait ekstraksi informasi dokumen dan sistem multi-agent.

BAB II LANDASAN TEORI

Bab ini menguraikan landasan teoretis yang mendukung penelitian, dimulai dari konsep semi-structured data dan data entry. Pembahasan mendalam dilakukan pada teknologi Large Language Model (LLM) yang mencakup arsitektur Transformer, metode fine-tuning (instruction dan LoRA), hingga Vision Language Model (VLM). Selanjutnya, dijelaskan pula konsep Agentic AI dan Multi-Agent System (MAS) dengan pendekatan hierarchical agent teams, Human-in-the-Loop

Page 10
<page_number>7</page_number>

(HITL), serta Model Context Protocol (MCP). Bagian akhir bab ini memaparkan perangkat pengembangan seperti SQLite, React Native, dan Expo, serta metodologi Agile Scrum dan blackbox sebagai teknik pengujian sistem

BAB III METODOLOGI PENELITIAN

Bab ini menjelaskan secara rinci langkah-langkah kerja yang dilakukan dalam penelitian. Cakupannya meliputi metode pengumpulan data, metode pengembangan sistem menggunakan Agile Scrum, waktu dan tempat penelitian, analisis kebutuhan sistem secara fungsional dan nonfungsional, serta rancangan sistem yang mencakup rancangan arsitektur sistem, rancangan proses, rancangan data, dan rancangan antarmuka pengguna.

BAB IV HASIL IMPLEMENTASI DAN PENGUJIAN SISTEM

Bab ini menyajikan implementasi sistem secara detail, analisis hasil fine-tuning GLM-OCR, evaluasi kinerja ekstraksi menggunakan KIEval dan ANLS*, evaluasi kinerja agent menggunakan AST accuracy dan Pass@K, serta pembahasan hasil pengujian blackbox.

BAB IV PENUTUP

Bab ini memuat kesimpulan dari penelitian yang telah dilakukan serta saran untuk pengembangan sistem selanjutnya.

1.7 Tinjauan Pustaka

Berikut rangkuman penelitian terdahulu yang berkaitan dengan otomatisasi data entry struk pembelian, teknologi Optical Character Recognition (OCR), ekstraksi informasi dokumen, serta penerapan Agentic AI dan arsitektur multi-agent yang menjadi rujukan dalam penyusunan penelitiawn ini.

Penelitian pertama dilakukan oleh Setiawan dkk., 2025 dengan judul "Ekstraksi Informasi Struk Belanja Melalui Pemanfaatan Tesseract dan Regular Expressions". Penelitian tersebut membangun sistem ekstraksi struk belanja untuk membantu proses pencatatan keuangan dengan menerapkan model YOLO untuk mendeteksi area struk, Tesseract untuk mengekstrak teks dari gambar, dan Regular Expressions untuk mengolah data menjadi terstruktur berupa nama produk, kuantitas, harga satuan, total harga, dan diskon. Hasil pengujian beta menggunakan

Page 11
<page_number>8</page_number>

User Acceptance Testing terhadap 37 responden menunjukkan rata-rata nilai 4,47 dari skala 5, namun sistem ini masih bergantung pada aturan parsing yang telah ditetapkan (rule-based) yang kurang adaptif terhadap variasi format struk yang berbeda, serta hasil ekstraksi Tesseract menjadi kurang akurat pada kondisi struk yang terlipat, buram, atau mengandung banyak noise, dan keluaran sistem hanya berhenti pada tampilan data terstruktur tanpa kemampuan untuk secara otomatis memasukkan data ke dalam sistem pencatatan seperti spreadsheet atau database.

Penelitian kedua dilakukan oleh Yan dkk., 2025 dan dipublikasikan pada tahun 2024 di jurnal Information Processing & Management (Elsevier) dengan judul "DocExtractNet: A Novel Framework for Enhanced Information Extraction from Business Documents". Penelitian tersebut mengembangkan framework berbasis LayoutLMv3 dengan tiga modul tambahan, yaitu ImageEnhance untuk pengenalan citra berkualitas rendah, PrecisionHints untuk melengkapi pasangan kunci-nilai yang hilang, dan CrossModalFusion untuk menggabungkan fitur citra dan teks. Hasil evaluasi menunjukkan bahwa DocExtractNet mencapai F1 sebesar 97,07% pada Finance-Receipts, 91,80% pada FUNSD, dan 97,38% pada CORD. Penelitian ini merepresentasikan kemajuan terkini dalam KIE multimodal berbasis Transformer yang memerlukan tahapan OCR terpisah dan tidak menangani alur hilir berupa entri data otomatis.

Penelitian ketiga dipublikasikan pada tahun 2025 di jurnal Scientific Reports (Nature) dengan judul "LLM-TKIE: Large Language Model Driven Transferable Key Information Extraction Mechanism for Nonstandardized Tables". Metode yang digunakan meliputi pipeline deteksi teks dan pengenalan teks, diikuti oleh penalaran semantik berbasis LLM dengan few-shot learning tanpa fine-tuning. Hasil yang diperoleh menunjukkan F1 sebesar 80,9% dan TED-accuracy 88,85% pada dataset CORD, serta F1 sebesar 83,9% pada SROIE tanpa proses fine-tuning. Pendekatan ini mengungguli model multimodal state-of-the-art sebesar 5–8% pada data domain yang belum diberi label, namun tidak menggunakan VLM end-to-end dan tidak menangani proses entri data hilir (Hu dkk., 2025).

Penelitian keempat dilakukan pada tahun 2024 dan dipublikasikan di arXiv dengan judul "STNet: See then Tell: Enhancing Key Information Extraction with

Page 12
<page_number>9</page_number>

*Vision Grounding". Model yang diusulkan bersifat OCR-free dan menggunakan token khusus untuk vision grounding serta physical decoder yang terspesialisasi. GPT-4 dimanfaatkan untuk konstruksi dataset pelatihan. Hasil evaluasi menunjukkan pencapaian state-of-the-art pada benchmark CORD, SROIE, dan DocVQA. Penelitian ini merepresentasikan batas kemampuan terkini dalam KIE tanpa OCR, namun tidak mencakup integrasi dengan sistem agent untuk otomatisasi data entry (S. Liu dkk., 2025).

Penelitian kelima dilakukan oleh Kim dkk., 2022 dan dipresentasikan di ECCV 2022 dengan judul "OCR-free Document Understanding Transformer (Donut)". Model yang diusulkan merupakan Transformer encoder-decoder yang memetakan citra dokumen langsung ke token JSON terstruktur tanpa memerlukan OCR, dan di-pre-train menggunakan generator data sintetis SynthDoG. Donut mencapai hasil state-of-the-art pada CORD document parsing, klasifikasi RVL-CDIP, dan DocVQA, serta mengungguli metode berbasis OCR dalam hal kecepatan dan akurasi. Penelitian ini merupakan karya seminal dalam pendekatan OCR-free yang menjadi fondasi bagi pengembangan VLM untuk pemahaman dokumen.

Penelitian keenam dilakukan oleh Zheng dkk., 2024 dan dipublikasikan di ACL 2024 System Demonstrations dengan judul "LlamaFactory: Unified Efficient Fine-Tuning of 100+ Language Models". LLaMA Factory merupakan framework terpadu yang mengintegrasikan berbagai teknik adaptasi model termasuk LoRA, QLoRA, GaLore, BAdam, dan freeze-tuning untuk lebih dari 100 LLM dan VLM. Framework ini juga menyediakan antarmuka web LlamaBoard serta mendukung pelatihan SFT, RLHF, DPO, dan ORPO. Hasil evaluasi menunjukkan bahwa LoRA dan QLoRA mencapai performa terbaik dibandingkan full fine-tuning pada sebagian besar kasus. Penelitian ini menjadi fondasi teknis bagi proses fine-tuning GLM-OCR dalam penelitian yang diusulkan.

Penelitian ketujuh dilakukan oleh Hong dkk., 2024 dan dipresentasikan sebagai Oral paper (1,2% teratas) di ICLR 2024 dengan judul "MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework". MetaGPT mengkodekan Standardized Operating Procedures (SOP) ke dalam urutan prompt untuk kolaborasi multi-agent, dengan pembagian peran spesialis dalam paradigma

Page 13
<page_number>10</page_number>

lini perakitan. Hasil evaluasi menunjukkan pencapaian state-of-the-art pada HumanEval dan MBPP dengan peningkatan absolut 5,4% pada MBPP melalui umpan balik eksekutif, serta pengurangan cascading hallucinations melalui keluaran antara yang terstruktur. Penelitian ini menjadi acuan utama untuk pola arsitektur hierarchical multi-agent yang diadaptasi dalam penelitian ini dengan konteks pemrosesan dokumen dan penggunaan MCP sebagai tool.

Penelitian kedelapan dilakukan oleh Wu dkk., 2023 dari Microsoft Research dan Penn State pada tahun 2023, dipublikasikan di COLM 2024 dengan judul "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation". AutoGen menggunakan konsep conversable agents yang mendukung LLM, masukan manusia, dan tool dalam pola percakapan yang dapat dikonfigurasi, serta menyediakan dukungan Human-in-the-Loop secara native. Sistem ini telah didemonstrasikan pada berbagai domain termasuk matematika, coding, tanya-jawab, dan pengambilan keputusan, serta menempati peringkat pertama pada benchmark GAIA. Penelitian ini menjadi referensi penting untuk integrasi HITL dalam sistem multi-agent, yang dalam penelitian ini diimplementasikan menggunakan mekanisme interrupt pada LangGraph.

Penelitian kesembilan dilakukan oleh Patil dkk., 2025 dari UC Berkeley dan dipublikasikan di ICML 2025 dengan judul "The Berkeley Function Calling Leaderboard (BFCL): From Tool Use to Agentic Evaluation of Large Language Models". BFCL merupakan benchmark untuk mengevaluasi kemampuan function-calling LLM menggunakan perbandingan Abstract Syntax Tree (AST). Evaluasi AST menangkap kebenaran fungsi yang dipanggil, nama parameter, dan tipe parameter tanpa memerlukan eksekusi. Benchmark ini mencakup lebih dari 2.200 kasus uji lintas Python, Java, JavaScript, dan SQL. Hasil evaluasi menunjukkan bahwa model terbaik unggul pada panggilan single-turn namun masih menghadapi tantangan pada penalaran multi-step. Metrik AST accuracy dari penelitian ini diadopsi sebagai salah satu metrik evaluasi kinerja agent dalam penelitian yang diusulkan.

Penelitian kesepuluh dilakukan oleh Khang dkk., 2025 dari Upstage AI dan dipublikasikan di ICDAR 2026 dengan judul *"KIEval: Evaluation Metric for

Page 14
<page_number>11</page_number>

*Document Key Information Extraction". KIEval merupakan metrik berorientasi aplikasi yang mengevaluasi kualitas ekstraksi pada tingkat entitas dan tingkat grup secara bersamaan, menggunakan algoritma Hungarian matching antara grup prediksi dan ground truth. Hasil evaluasi menunjukkan bahwa metrik Entity F1 konvensional memberikan skor 1,0 bahkan ketika pengelompokan salah, namun KIEval mampu memberikan penalti terhadap ketidaksesuaian struktural secara tepat. Metrik ini sangat relevan untuk evaluasi ekstraksi struk pembelian karena hubungan antara nama item, kuantitas, dan harga harus dipertahahkan secara struktural.

Penelitian kesebelas dilakukan oleh Peer dkk., 2025 dari DeepOpinion pada tahun 2025 dan dipublikasikan di arXiv dengan judul "ANLS - A Universal Document Processing Metric for Generative Large Language Models". ANLS* memperluas metrik ANLS klasik untuk menangani struktur keluaran yang kompleks dengan memetakan prediksi dan ground truth ke dalam struktur pohon (tree). Metrik ini mendukung perbandingan string, tuple, list, dan dictionary dengan penalti terhadap halusinasi. Hasil evaluasi dilakukan menggunakan GPT-4, Claude-3, dan Gemini pada tujuh dataset dokumen termasuk SROIE dan VRDU. Kemampuan ANLS* dalam menangani keluaran JSON bersarang menjadikannya sangat relevan untuk mengevaluasi skema ekstraksi struk pembelian yang memiliki struktur hierarkis seperti info, items, dan payment.

Rangkuman dari beberapa penelitian terdahulu yang telah dijelaskan sebelumnya dapat dilihat pada Tabel 1.1 berikut.

Tabel 1. 1 Tinjauan penelitian terdahulu

No.	Judul	Metode	Hasil
1.	Ekstraksi Informasi Struk Belanja Melalui Pemanfaatan Tesseract dan Regular Expressions	YOLO untuk deteksi area struk, Tesseract OCR untuk ekstraksi teks, dan Regular Expressions untuk parsing data terstruktur	Pengujian hanya pada deteksi layout struk dengan F1 score 0.88, tanpa melakukan evaluasi pada hasil proses ekstrasi berbasis regex.
Page 15
<page_number>12</page_number>

2.	DocExtractNet: A Novel Framework for Enhanced Information Extraction from Business Documents	LayoutLMv3 dengan modul Image Enhance, Precision Hints, dan Cross Modal Fusion	F1 score 97,07% pada Finance-Receipts, 91,80% pada FUNSD, 97,38% pada CORD
3.	LLM-TKIE: Large Language Model Driven Transferable Key Information Extraction	Pipeline deteksi teks + pengenalan teks, diikuti penalaran LLM dengan few-shot learning	F1 80,9% pada CORD; F1 83,9% pada SROIE tanpa fine-tuning
4.	STNet: See then Tell: Enhancing KIE with Vision Grounding	Model OCR-free dengan token vision grounding dan physical decoder	State-of-the-art pada CORD, SROIE, dan DocVQA
5.	Donut: OCR-free Document Understanding Transformer	Transformer encoder-decoder yang memetakan citra dokumen langsung ke token JSON	State-of-the-art pada CORD, RVL-CDIP, dan DocVQA
6.	LlamaFactory: Unified Efficient Fine-Tuning of 100+ Language Models	Framework terpadu dengan LoRA, QLoRA, GaLore, BAdam untuk 100+ LLM/VLM	LoRA dan QLoRA mencapai performa terbaik vs. full fine-tuning
7.	MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework	Standardized Operating Procedures (SOP) dalam prompt multi-agent hierarkis	State-of-the-art pada HumanEval dan MBPP; peningkatan 5,4% pada MBPP
8.	AutoGen: Enabling Next-Gen LLM	Conversable agents dengan HITL native dan	Peringkat #1 pada benchmark GAIA
Page 16
<page_number>13</page_number>

Applications via Multi-Agent Conversation	pola percakapan yang dapat dikonfigurasi	
9.	BFCL: From Tool Use to Agentic Evaluation of LLMs	Evaluasi function-calling menggunakan perbandingan Abstract Syntax Tree (AST)	2.200+ kasus uji; AST accuracy berkorelasi dengan executable accuracy
10.	KIEval: Evaluation Metric for Document Key Information Extraction	Metrik evaluasi entity-level dan group-level dengan Hungarian matching	Mendeteksi kesalahan struktural yang tidak tertangkap oleh Entity F1 konvensional
11.	ANLS*: A Universal Document Processing Metric for Generative LLMs	Perbandingan struktur pohon untuk string, tuple, list, dan dictionary	Evaluasi pada 7 dataset dengan GPT-4, Claude-3, dan Gemini
Berdasarkan tinjauan pustaka yang telah dikaji, penelitian-penelitian sebelumnya dalam domain pemrosesan struk pembelian memiliki beberapa keterbatasan fungsional yang belum terselesaikan. Dari sisi pengenalan dokumen, penelitian di Indonesia masih mengandalkan OCR konvensional berbasis Tesseract yang dikombinasikan dengan aturan parsing manual menggunakan Regular Expressions, di mana pendekatan ini tidak mampu memahami makna dan hubungan antar informasi pada struk secara kontekstual dan hanya mencocokkan pola teks yang telah ditentukan sebelumnya. Dari sisi dataset, benchmark yang umum digunakan seperti SROIE hanya berisi struk hasil pemindaian (scan) dengan kualitas seragam yang tidak merepresentasikan kondisi nyata saat pengguna memfotografi struk menggunakan kamera ponsel dengan variasi sudut pengambilan, pencahayaan, dan jarak yang beragam. Dataset CORD, meskipun berasal dari Indonesia, hanya berfokus pada struk restoran dengan informasi yang telah disederhanakan pada bagian item dan pembayaran, tanpa menampilkan elemen

Page 17
<page_number>14</page_number>

visual lainnya seperti informasi toko, kontak, nomor pajak, dan promosi yang pada kenyataannya hadir pada struk dan dapat mempersulit proses pengenalan. Dari sisi fungsionalitas, seluruh penelitian yang dikaji hanya berhenti pada tahap OCR dan pengenalan informasi dari struk tanpa menyediakan kemampuan untuk secara otomatis memasukkan data hasil pengenalan ke dalam sistem pencatatan seperti spreadsheet atau database, yang berarti pengguna masih harus menyalin data secara manual setelah proses pengenalan selesai. Oleh karena itu, diusulkan penelitian dengan judul "Otomatisasi Data Entry Struk Pembelian menggunakan Vision Language Model Fine-Tuned dengan LoRA dan Orkestrasi Hierarchical Multi-Agent berbasis Model Context Protocol (MCP)" yang tidak hanya mengenali informasi dari foto struk secara akurat menggunakan model kecerdasan buatan yang telah dilatih khusus untuk struk pembelian, tetapi juga secara otomatis memasukkan data tersebut ke dalam Google Sheets melalui sistem agent cerdas yang terkoordinasi, dilengkapi mekanisme konfirmasi oleh pengguna sebelum data disimpan untuk menjamin kebenaran pencatatan.

Page 18
BAB II
LANDASAN TEORI
2.1 Struk Pembelian
Struk pembelian atau nota belanja merupakan dokumen bukti transaksi keuangan yang dihasilkan dari aktivitas pembelian dan memuat informasi terstruktur mengenai detail transaksi. Secara teknis, struk berfungsi sebagai sumber data primer yang merekam atribut penting seperti nama entitas pedagang (merchant), deskripsi produk, kuantitas, harga satuan, nilai total belanja, metode pembayaran, hingga tanggal dan waktu transaksi. Dalam konteks document understanding, struk pembelian termasuk dalam kategori visually-rich document yang mengandung banyak nilai numerik dan memerlukan kemampuan discrete reasoning untuk menjawab pertanyaan terkait harga, kuantitas, dan total pembayaran (Begaev dan Orlov, 2023). Miliaran struk dicetak setiap tahun secara global untuk keperluan pencatatan pengeluaran, pengelolaan keuangan, dan pelaporan akuntansi, baik pada tingkat individu maupun organisasi (Rexhepi dkk., 2025).

Meskipun memiliki elemen informasi yang serupa secara semantik antar dokumen, struk pembelian menyajikan tantangan ekstraksi yang kompleks akibat karakteristik fisiknya yang khas. Variasi tata letak (layout) yang sangat dinamis antar sistem kasir, kualitas cetakan yang rentan pudar (faded), keberadaan derau (noise) pada citra hasil foto, serta perbedaan format representasi untuk entitas yang secara semantik identik, seperti tanggal, nama produk yang disingkat, dan format harga, menjadikan proses ekstraksi informasi dari struk tidak dapat diselesaikan dengan pencocokan pola statis semata. Kondisi ini mendorong kebutuhan akan pendekatan berbasis deep learning yang mampu memetakan citra struk secara langsung menjadi structured key-value fields yang akurat, tanpa bergantung pada aturan ekstraksi yang telah ditentukan sebelumnya untuk setiap format struk.

<page_number>15</page_number>

Page 19
<page_number>16</page_number>

2.2 Semi-Structured Data
Semi-structured data merupakan kategori data yang tidak mengikuti skema relasional yang kaku seperti tabel database, namun memiliki struktur parsial berupa tag, hierarki, atau penanda yang membedakannya dari data tidak terstruktur sepenuhnya (Li, Jiang dan Song, 2023). Berbeda dengan structured data di mana setiap field telah terdefinisi secara eksplisit dan konsisten, semi-structured data memiliki variasi dalam tata letak, urutan kemunculan field, dan kelengkapan informasinya antar dokumen.

Struk pembelian merupakan salah satu contoh semi-structured data yang paling umum ditemui dalam lingkup bisnis ritel. Setiap struk mengandung elemen informasi yang serupa secara semantik, seperti nama toko, tanggal transaksi, daftar item, dan total pembayaran, namun format visualnya sangat bervariasi antar merchant (Ylisiurunen, 2022). Variasi ini mencakup perbedaan tipografi, layout kolom, penempatan logo, penggunaan singkatan nama produk, serta representasi harga dan tanggal yang beragam bergantung pada sistem kasir yang digunakan oleh masing-masing merchant.

Tantangan utama dalam pemrosesan semi-structured data pada dokumen bisnis adalah ketidakkonsistenan representasi untuk entitas yang secara semantik identik. Tanggal yang sama dapat direpresentasikan sebagai "01/01/2025", "1 Januari 2025", atau "2025-01-01". Nama produk dapat disingkat atau dieja lengkap. Kondisi ini menjadikan pemrosesan struk pembelian sebagai permasalahan Key Information Extraction (KIE) yang membutuhkan pemahaman kontekstual, bukan sekadar pencocokan pola berbasis aturan statis (Abdalla dkk., 2025).

Karakteristik visually-rich document pada struk pembelian menambahkan dimensi kompleksitas tersendiri. Posisi spasial elemen teks dalam ruang dua dimensi membawa makna semantik yang tidak kalah penting dari konten teksnya. Informasi header toko di bagian atas, daftar item di tengah, dan ringkasan pembayaran di bawah membentuk struktur visual yang konsisten secara semantik meskipun variatif secara visual antar dokumen (Nathan, 2025).

Page 20
<page_number>17</page_number>

2.3 Data Entry
Data entry didefinisikan sebagai serangkaian proses terstruktur yang bertujuan untuk memastikan data yang diterima, dimasukkan, diproses, dan dikelola dalam suatu sistem bersifat akurat, lengkap, konsisten, reliabel, dan layak untuk dianalisis secara statistik. Tidak hanya terbatas pada aktivitas memasukkan data ke dalam sistem, data entry mencakup tahapan yang lebih luas seperti penerimaan dan pelacakan data, proses input, validasi, pembersihan data, pengendalian perubahan, hingga rekonsiliasi dan transfer data ke basis data akhir (Society for Clinical Data Management, 2023).

Kualitas hasil data entry dapat diukur melalui enam dimensi utama, yaitu akurasi, kelengkapan, konsistensi, ketepatan waktu, validitas, dan keunikan data (Syed dkk., 2023). Proses manual yang dilakukan oleh operator manusia rentan terhadap penurunan kualitas pada keenam dimensi tersebut, terutama ketika volume dokumen yang harus diproses tinggi dan pekerjaan bersifat repetitif.

Penelitian empiris menunjukkan bahwa entri data manual memiliki tingkat kesalahan signifikan yang berkisar antara 1% hingga 4% per field, bahkan dapat mencapai 26,9% pada kondisi tertentu akibat faktor kelelahan dan distrase manusia (Mays dan Mathias, 2019; Barchard dkk., 2020). Fenomena ini menegaskan bahwa metode konvensional seperti visual checking menghasilkan risiko kesalahan yang jauh lebih tinggi dibandingkan pendekatan otomatis, sehingga mengancam integritas kualitas data organisasi secara keseluruhan. Tingkat kesalahan ini, meskipun tampak kecil pada skala individual, dapat mengakibatkan ketidakakuratan yang signifikan dalam laporan keuangan apabila tidak terdeteksi dan terkoreksi lebih awal. Selain itu, proses manual membutuhkan waktu pemrosesan yang jauh lebih lama dibandingkan dengan pendekatan otomatis, sehingga menjadi hambatan dalam alur kerja yang membutuhkan kecepatan tinggi.

Perkembangan teknologi telah mendorong evolusi pendekatan otomatisasi data entry dari rule-based Optical Character Recognition (OCR) tradisional, menuju sistem berbasis machine learning, hingga pendekatan terkini yang memanfaatkan Large Language Model (LLM) dan model multimodal (Khanchandani dkk., 2026). Keterbatasan OCR tradisional dalam menangani

Page 21
<page_number>18</page_number>

variasi layout dan kualitas gambar yang rendah menjadi pendorong utama adopsi pendekatan berbasis AI yang lebih adaptif dan dapat menggeneralisasi lintas format dokumen.

2.4 Large Language Models (LLM)
Large Language Models (LLM) didefinisikan sebagai model bahasa berbasis jaringan saraf dalam dengan jumlah parameter yang sangat besar, umumnya berkisar dari miliaran hingga ratusan triliun parameter, yang dilatih pada korpus teks berskala masif, dengan dibangun di atas arsitektur Transformer (Zhao dkk., 2026). Karakteristik utama LLM adalah kemampuan general-purpose language understanding and generation yang diperoleh melalui pelatihan miliaran parameter model pada data teks masif, sebagaimana diprediksi oleh scaling laws (Minaee dkk., 2025). Evolusi model bahasa dapat ditelusuri dari statistical language models, neural language models, pre-trained language models (PLMs), hingga LLM yang menunjukkan kemampuan khusus (special abilities) yang tidak ditemukan pada model dengan skala lebih kecil ketika skala parameter melampaui ambang batas tertentu.

Salah satu kemampuan utama LLM yang relevan untuk pengembangan sistem agentic adalah kemampuan instruction-following, yaitu kemampuan model untuk memahami dan mengeksekusi instruksi yang diberikan dalam bahasa alami (Wang dkk., 2025). Kemampuan ini memungkinkan LLM berperan sebagai mesin pengambil keputusan dalam sistem agent, menentukan langkah-langkah eksekusi yang perlu dilakukan untuk menyelesaikan tugas yang diberikan pengguna tanpa memerlukan pemrograman eksplisit untuk setiap skenario.

LLM modern juga memiliki kemampuan zero-shot dan few-shot generalization, di mana model dapat menangani tugas baru tanpa pelatihan ulang, hanya dengan diberikan contoh atau instruksi dalam konteks prompt (Brown dkk., 2020). Kemampuan ini sangat relevan dalam pengembangan sistem agent yang perlu menangani variasi input pengguna yang luas dan tidak terprediksi sepenuhnya.

Page 22
<page_number>19</page_number>

Dalam penelitian ini, LLM digunakan dalam dua peran yang berbeda. Pertama, sebagai model dasar untuk GLM-OCR yang kemudian diadaptasi melalui proses fine-tuning menggunakan data struk pembelian untuk tugas ekstraksi terstruktur. Kedua, sebagai model orkestrasi untuk Supervisor Agent, SQL Agent, Data Entry Team Agent, dan Guardrails menggunakan Gemini 3.1 Pro yang mengkoordinasikan seluruh alur kerja sistem.

2.5 Transformers
Arsitektur Transformer diperkenalkan oleh Vaswani dkk., 2023 sebagai model sequence-to-sequence yang sepenuhnya berbasis mekanisme attention, tanpa menggunakan rekurensi maupun konvolusi. Pendekatan ini menjadi terobosan fundamental dalam pemrosesan bahasa alami karena memungkinkan komputasi dependensi antar posisi secara paralel dengan jumlah operasi sekuensial yang konstan, berbeda dengan Recurrent Neural Networks (RNN) yang memerlukan O(n) operasi sekuensial. Keberhasilan Transformer pada tugas machine translation dengan pencapaian 28,4 BLEU pada WMT 2014 English-to-German dan 41,8 BLEU pada WMT 2014 English-to-French telah menjadikannya arsitektur dominan tidak hanya dalam pemrosesan bahasa alami, tetapi juga dalam computer vision, pemrosesan audio, dan berbagai disiplin ilmu lainnya (Lin dkk., 2022).

Arsitektur Transformer terdiri dari dua komponen utama, yaitu encoder dan decoder, yang masing-masing disusun dari tumpukan L blok identik. Setiap blok encoder tersusun dari dua sub-lapisan utama: modul multi-head self-attention dan jaringan position-wise feed-forward network (FFN). Pada setiap sub-lapisan tersebut, diterapkan koneksi residual (residual connection) yang diikuti oleh Layer Normalization untuk memfasilitasi pelatihan model yang lebih dalam. Secara formal, setiap blok encoder dapat dituliskan sebagai berikut.

H' = LayerNorm(SelfAttention(X) + X) (2. 1)

H = LayerNorm(FFN(H') + H') (2. 2)

dengan SelfAttention(·) menyatakan modul self-attention, LayerNorm(·) menyatakan operasi layer normalization, X adalah keluaran dari lapisan

Page 23
<page_number>20</page_number>

sebelumnya, H' adalah keluaran sub-lapisan attention, dan H adalah keluaran akhir blok encoder.

Blok decoder memiliki struktur yang serupa dengan blok encoder, namun dengan penambahan sub-lapisan ketiga berupa modul cross-attention yang ditempatkan di antara modul self-attention dan FFN. Modul cross-attention ini memungkinkan setiap posisi pada decoder untuk mengakses seluruh posisi pada keluaran encoder. Selain itu, modul self-attention pada decoder dimodifikasi dengan mekanisme masking untuk mencegah setiap posisi mengakses informasi dari posisi-posisi berikutnya, sehingga prediksi untuk posisi i hanya bergantung pada keluaran yang telah diketahui pada posisi kurang dari i. Mekanisme ini sering disebut sebagai autoregressive atau causal attention. Arsitektur keseluruhan Transformer yang terdiri dari encoder (kiri) dan decoder (kanan) dengan komponen multi-head attention, feed-forward network, residual connection, dan layer normalization, ditunjukkan pada Gambar 2.1.

<img>Arsitektur Transformer (diadaptasi dari Vaswani dkk., 2023)</img>

GAMBAR 2.1 ARSITEKTUR TRANSFORMER (DIADAPTASI DARI VASWANI DKK., 2023)

Secara umum, arsitektur Transformer dapat digunakan dalam tiga cara, yaitu encoder-decoder untuk pemodelan sequence-to-sequence seperti machine translation, encoder only untuk tugas klasifikasi atau pelabelan sekuens seperti

Page 24
<page_number>21</page_number>

yang digunakan pada BERT, dan decoder only untuk pembangkitan sekuens seperti pemodelan bahasa pada keluarga GPT.

Komponen inti Transformer adalah mekanisme Multi-Head Self-Attention yang memungkinkan model memperhatikan bagian-bagian berbeda dari input secara simultan dan dari berbagai perspektif representasi. Secara formal, operasi attention dihitung sebagai berikut.

$Attention(Q, K, V) = softmax\left(\frac{QK^T}{\sqrt{D_k}}\right)V = AV \quad (2.3)$

dengan N dan M menyatakan panjang queries dan keys (atau values), $D_K$ dan $D_V$ menyatakan dimensi keys (atau queries) dan values, serta $A = softmax\left(\frac{QK^T}{\sqrt{D_k}}\right)$ yang disebut sebagai matriks attention. Fungsi softmax diterapkan secara baris (row-wise). Pembagian hasil dot-product dengan $\sqrt{D_k}$ dilakukan untuk mengatasi masalah vanishing gradient pada fungsi softmax, karena untuk nilai $D_k$ yang besar, hasil dot-product memiliki magnitudo yang besar sehingga mendorong fungsi softmax ke wilayah dengan gradien yang sangat kecil.

Pemahaman arsitektur Transformer relevan dalam konteks penelitian ini karena teknik fine-tuning Low-Rank Adaptation (LoRA) yang digunakan bekerja secara langsung pada lapisan-lapisan linear dalam arsitektur Transformer. LoRA menambahkan matriks bobot low-rank pada lapisan proyeksi attention Q dan V untuk mengadaptasi perilaku model ke domain spesifik tanpa memodifikasi seluruh parameter model yang sudah dilatih.

2.6 Instruction Fine-Tuning dan Parameter-Efficient Fine-Tuning
Perkembangan paradigma pemrosesan bahasa alami telah bergeser dari sekadar pembelajaran representasi bahasa universal menuju teknik adaptasi yang lebih presisi dan efisien (Radford dkk., 2018). Meskipun pre-training memberikan fondasi pengetahuan yang luas, model bahasa berskala besar seringkali memerlukan fase penyesuaian tambahan agar dapat menyelaraskan (align) kemampuannya dengan instruksi spesifik pengguna serta batasan sumber daya komputasi (Qiu dkk., 2020). Dalam konteks ini, Instruction Fine-Tuning (IFT) dan Parameter-Efficient Fine-Tuning (PEFT) muncul sebagai metodologi kunci

Page 25
<page_number>22</page_number>

yang berfokus untuk peningkatan kemampuan model dalam mengikuti perintah kontekstual secara akurat dan optimasi yang memungkinkan adaptasi model pada tugas hilir dengan hanya memodifikasi sebagian kecil parameter model.

2.6.1 Instruction Fine-Tuning (IFT)

Instruction fine-tuning, yang juga dikenal sebagai supervised instruction fine-tuning, merupakan proses untuk meningkatkan kemampuan LLM dalam mengikuti instruksi spesifik dan menghasilkan respons yang diinginkan (Parthasarathy dkk., 2024). Berbeda dengan pre-training di mana LLM dilatih untuk menghasilkan satu kata pada satu waktu melalui penyelesaian teks (text completion), instruction fine-tuning berfokus pada menggunakan data berlabel yang dirancang untuk mengajarkan model mengikuti jenis instruksi tertentu secara akurat dan konsisten (Raschka, 2025).

Proses IFT mengoptimalkan model dengan meminimalkan cross-entropy loss (atau negative log-likelihood) antara distribusi token yang diprediksi model dengan respons target (Ouyang dkk., 2022; Wei dkk., 2022), yang didefinisikan sebagai:

$$\mathcal{L}{IFT} = -\sum{t=1}^{T} \log P_\theta(y_t | x, y_{<t})$$ (2. 4)

di mana x adalah instruksi yang diberikan, yt adalah token ke-t dari respons target, y<t adalah token respons sebelum posisi t, dan θ adalah parameter model yang dioptimalkan.

Motivasi penggunaan IFT dalam penelitian ini adalah adanya ketidaksesuaian antara output default GLM-OCR dengan skema JSON yang dibutuhkan sistem. Pada percobaan awal, GLM-OCR tanpa fine-tuning menghasilkan output yang tidak konsisten dalam format field, menggunakan nama field yang berbeda dari skema yang ditetapkan, dan melewati sejumlah field yang seharusnya diisi meskipun informasinya tersedia dalam gambar. Melalui IFT, model diajarkan untuk selalu menghasilkan output yang sesuai dengan skema ekstrasi yang sudah didefinisikan.

Page 26
<page_number>23</page_number>

2.6.2 Low-Rank Adaptation (LoRA)
Low-Rank Adaptation (LoRA) merupakan teknik Parameter-Efficient Fine-Tuning (PEFT) yang diperkenalkan oleh (Hu dkk., 2021) sebagai solusi untuk permasalahan computational cost yang tinggi pada full fine-tuning LLM berskala besar dengan cara membekukan bobot model pre-trained dan menyuntikkan matriks dekomposisi rank rendah yang dapat dilatih ke dalam setiap lapisan arsitektur Transformer. LoRA memungkinkan adaptasi model pra-latih ke domain spesifik dengan jumlah parameter yang dapat dilatih jauh lebih sedikit, tanpa mengorbankan kualitas adaptasi secara signifikan.

Ide dasar LoRA berangkat dari hipotesis bahwa pembaruan bobot yang diperlukan selama fine-tuning memiliki rank intrinsik yang rendah. Dengan kata lain, perubahan yang dibutuhkan untuk mengadaptasi model ke tugas baru dapat direpresentasikan dalam ruang berdimensi rendah. Alih-alih memperbarui seluruh matriks bobot $W_0 \in R^{d \times k}$, LoRA membekukan bobot asli dan menambahkan dekomposisi low-rank yang dapat dilatih.

$W' = W + \Delta W = W + BA$ (2.)

di mana $B \in R^{d \times r}$ dan $A \in R^{r \times k}$ dengan rank $r \ll \min(d, k)$. Selama proses fine-tuning, hanya matriks A dan B yang dilatih sementara bobot asli W tetap dibekukan. Matriks A diinisialisasi menggunakan distribusi acak Gaussian dan matriks B diinisialisasi dengan nilai nol, sehingga pada awal pelatihan $\Delta W = 0$ yang menjamin perilaku model pada tahap awal identik dengan model dasar. Sehingga output akhir lapisan dengan LoRA dihitung sebagai berikut.

$h = W_0 x + \Delta W x = W_0 x + B Ax$ (2.5)

dengan $B \in R^{d \times r}$ dan $A \in R^{r \times k}$ adalah matriks dekomposisi rank rendah dengan rank $r \ll \min(d, k)$, $W_0$ dibekukan dan tidak menerima pembaruan gradien, sedangkan A dan B merupakan parameter yang dapat dilatih. Matriks A diinisialisasi dengan distribusi Gaussian acak dan B diinisialisasi dengan nol, sehingga $\Delta W = BA$ bernilai nol pada awal pelatihan. Keluaran $\Delta W x$ kemudian diskalakan dengan $\frac{\alpha}{r}$, di mana $\alpha$ adalah konstanta terhadap r. Pada gambar Gambar 2.2 menunjukan

Page 27
<page_number>24</page_number>

ilustrasi reparameterisasi LoRA yang menunjukkan matriks bobot pre-trained W₀ yang dibekukan dan matriks dekomposisi low-rank A dan B yang dapat dilatih.

<img>A diagram illustrating the Low-Random-Access (LoRA) parameterization technique. It shows a blue box labeled "Pretrained Weights" with dimensions (W \in \mathbb{R}^{d \times d}). Above this box is a yellow bar labeled "h". To the right, an orange diamond labeled "B = 0" is connected to the blue box by a plus sign. Below the blue box, another orange diamond labeled "A = N(0, \sigma^2)" is connected to the blue box by a minus sign. At the bottom, a yellow bar labeled "x" is connected to the blue box by a "d" label.</img>

Gambar 2. 2 Ilustrasi reparameterisasi LoRA (diadaptasi dari Hu dkk., 2021)

Keunggulan utama LoRA terletak pada efisiensi parameter yang signifikan. Sebagai ilustrasi, untuk model dengan dimensi (d = 4096) dan rank (r = 16), LoRA hanya memerlukan sekitar 0,1% jumlah parameter yang perlu dilatih dibandingkan full fine-tuning pada lapisan yang sama. Efisiensi ini memungkinkan fine-tuning dilakukan pada perangkat dengan kapasitas memori GPU yang terbatas dan mempercepat proses pelatihan secara keseluruhan.

Dalam penelitian ini, LoRA diterapkan pada lapisan proyeksi Q dan V dari mekanisme Multi-Head Attention pada model GLM-OCR. Pemilihan rank r dilakukan melalui serangkaian eksperimen untuk menemukan keseimbangan optimal antara kapasitas adaptasi model dan efisiensi komputasi yang tersedia.

2.6.3 LLaMA Factory
LLaMA Factory merupakan sebuah kerangka kerja (framework) terpadu yang dirancang untuk memfasilitasi proses fine-tuning yang efisien terhadap lebih dari 100 model bahasa besar (LLM). Dikembangkan oleh (Zheng dkk., 2024), framework ini mengintegrasikan berbagai teknik adaptasi model terkini ke dalam satu sistem yang skalabel, memungkinkan pengembang untuk melakukan instruction tuning tanpa perlu membangun infrastruktur pelatihan dari awal.

Page 28
<page_number>25</page_number>

Arsitektur LLaMA Factory memisahkan komponen manajemen data, pemilihan model, dan algoritma optimasi, sehingga memberikan fleksibilitas tinggi dalam mengelola alur kerja pelatihan model secara sistematis dan terstandarisasi, yang dapat ditunjukan pada Gambar 2.3.

<img>A diagram showing the architecture of LLaMA Factory. It includes a top-level "LlamaBoard" with two components: "Experiment Configurator" and "Training Status Monitor". These connect to a central "Trainer" box. The Trainer has two sub-boxes: "Optimization" containing "LoRA", "PiSSA", "GaLore", and "BAdam"; and "Approaches" containing "Pre-train", "SFT", "RLHF", and "DPO". Below the Trainer is a "Model Loader" box with four sub-boxes: "Initialization", "Patches", "Quantization", and "Adapters", which connects to "Pre-Trained Models". To the right of the Trainer is a "Data Worker" box with four sub-boxes: "Loading", "Aligning", "Merging", and "Preprocess", which connects to "Conversational Datasets".</img>

Gambar 2. 3 Arsitektur LLaMA Factory (diadaptasi dari Zheng dkk., 2024)

Efisiensi yang ditawarkan oleh LLaMA Factory terletak pada kemampuannya untuk menggabungkan teknik PEFT, seperti LoRA, dengan optimasi memori tingkat lanjut, di mana fitur-fitur yang dimanfaatkan mencakup dukungan native untuk model multimodal dan integrasi format dataset percakapan yang kompleks. Selain itu, framework ini memungkinkan pemantauan metrik pelatihan secara real-time dan mendukung mixed-precision training dengan format bfl6 yang secara signifikan menurunkan kebutuhan memori GPU tanpa mengorbankan stabilitas numerik selama proses pelatihan.

Fitur-fitur LLaMA Factory yang dimanfaatkan dalam penelitian ini mencakup dukungan native untuk model GLM-OCR sebagai model multimodal, integrasi format dataset percakapan multimodal yang mencakup pasangan gambar dan teks, implementasi LoRA dengan konfigurasi target modul yang fleksibel, serta monitoring metrik pelatihan dan validasi secara real-time.

Page 29
<page_number>26</page_number>

2.7 Vision Language Model (VLM)
*Vision Language Model (VLM) merupakan kelas model kecerdasan buatan yang dirancang untuk secara bersama memproses dan memahami informasi visual dan tekstual (Zhang dkk., 2024). Berbeda dari model tradisional yang menangani gambar atau teks secara independen, VLM dilatih pada dataset yang memasangkan gambar dengan keterangan, deskripsi, atau bentuk teks lainnya, sehingga mampu menjembatani kesenjangan antara persepsi visual dan pemahaman bahasa. Kemampuan ini memungkinkan VLM untuk melakukan berbagai tugas multimodal seperti image captioning, visual question answering (VQA), pengambilan berbasis teks (text-based retrieval), dan pembangkitan dialog berbasis gambar (image-grounded dialogue generation) (Verbovskiy, 2025).

Arsitektur VLM modern umumnya terdiri dari tiga komponen utama (Liu dkk., 2023). Komponen pertama adalah image encoder yang berfungsi mengekstraksi fitur visual dari gambar input ke dalam representasi berdimensi tinggi. Komponen kedua adalah language model (biasanya berupa LLM) yang berperan sebagai otak untuk pemrosesan semantik dan generasi teks. Komponen ketiga adalah connector atau projector yang berfungsi menjembatani perbedaan modalitas dengan memetakan fitur visual ke dalam ruang embedding yang dapat dipahami oleh language model. Contoh arsitektur VLM dapat diliat pada Gambar 2.4 yang merepresentasikan skema interaksi antara vision encoder, lapisan proyeksi, dan LLM dalam kerangka kerja LLaVA.*

<img>A diagram showing the architecture of a Vision Language Model (VLM). It includes a "Language Model f_φ" on the left, which projects to a "Vision Encoder" that processes an "Image X_v". The Vision Encoder outputs "H_v" and "Z_v", which are then projected by "W" to "H_q". This "H_q" is fed into a "Language Instruction X_q". From this point, the model generates a "Language Response X_a" through the Language Model.</img>

Gambar 2. 4 Contoh arsitektur VLM (diadaptasi dari H. Liu dkk., 2023)

Kemampuan VLM dalam memahami dokumen visual seperti struk pembelian melampaui OCR tradisional dalam beberapa aspek yang kritis (Kim dkk., 2022). VLM dapat memahami konteks visual dokumen secara holistik,

Page 30
<page_number>27</page_number>

menghubungkan informasi yang tersebar di berbagai bagian dokumen, serta menangani ambiguitas teks dengan memanfaatkan pemahaman visual tentang tata letak dan struktur dokumen (Xu dkk., 2020; Mathew, Karatzas dan Jawahar, 2021). Kemampuan ini menjadikan VLM sebagai pilihan yang lebih tepat untuk tugas KIE dari dokumen semi-structured yang memiliki variasi layout tinggi dibandingkan dengan pendekatan berbasis aturan atau OCR tradisional.

2.8 Visual Document Understanding (VDU)
Visual Document Understanding (VDU) merupakan bidang yang berkaitan dengan interpretasi dan pemahaman berbagai dokumen digital-natif atau hasil pemindaian, yang mencakup namun tidak terbatas pada formulir, tabel, laporan, dan makalah akademis. VDU secara fundamental bergantung pada kemampuan untuk mengekstraksi, mengenali, dan memahami informasi tekstual dan visual yang tertanam dalam dokumen, menjembatani kesenjangan antara dokumen fisik dan sistem digital. Berbeda dari tugas visi-bahasa konvensional, VDU secara khusus berkaitan dengan skenario yang kaya teks (text-rich scenarios) yang mengandung elemen dokumen yang berlimpah (X. Li dkk., 2024).

2.8.1 OCR Tradisional
Optical Character Recognition (OCR) merupakan teknologi yang digunakan untuk mengonversi berbagai jenis dokumen, seperti file kertas yang dipindai, dokumen PDF, atau gambar yang diambil oleh kamera digital, menjadi teks yang dapat diedit dan dicari. Dengan menganalisis bentuk dan pola karakter dalam suatu gambar, perangkat lunak OCR dapat mengekstraksi informasi tekstual dan membuatnya dapat digunakan untuk berbagai aplikasi, termasuk digitalisasi dokumen, otomasi entri data, dan pengambilan informasi (Verbovskiy, 2025).

Keterbatasan utama OCR tradisional dalam konteks pemrosesan struk pembelian terletak pada ketidakmampuannya memahami struktur semantik dokumen. OCR hanya menghasilkan teks mentah tanpa informasi tentang makna atau hubungan semantik antar elemen teks. Untuk mengekstrak informasi terstruktur dari output OCR tradisional, diperlukan tahapan lanjutan berupa Named

Page 31
<page_number>28</page_number>

Entity Recognition (NER) atau aturan berbasis ekspresi reguler yang tidak dapat menggeneralisasi dengan baik terhadap variasi format struk yang beragam.

Selain itu, akurasi OCR tradisional sangat bergantung pada kualitas gambar input. Foto struk dengan kondisi pencahayaan tidak merata, perspektif miring, resolusi rendah, atau teks yang tercetak pudar dapat menghasilkan output penuh kesalahan pengenalan karakter yang kemudian berdampak pada seluruh pipeline ekstraksi informasi hilirnya.

2.8.2 VLM-Based Document Understanding
Pendekatan berbasis VLM untuk pemahaman dokumen mengatasi keterbatasan OCR tradisional dengan memproses dokumen secara end-to-end, menggabungkan pengenalan teks dan pemahaman semantik dalam satu proses inferensi model (Guan dkk., 2026). Model berbasis pendekatan ini dilatih untuk memahami tata letak dokumen sebagai bagian integral dari pemahaman semantiknya, bukan sebagai langkah pra-pemrosesan yang terpisah.

Keunggulan utama pendekatan ini adalah kemampuan generalisasi yang lebih baik terhadap variasi format dokumen, toleransi yang lebih tinggi terhadap noise dan distorsi gambar, serta kemampuan untuk langsung menghasilkan output terstruktur tanpa pipeline pemrosesan tambahan (Bai dkk., 2023). Dalam evaluasi pada dokumen bisnis, model berbasis VLM menunjukkan performa yang secara konsisten lebih tinggi dibandingkan pipeline OCR tradisional pada tugas KIE, khususnya untuk dokumen dengan layout yang kompleks dan bervariasi (Huang dkk., 2022).

2.8.3 GLM-OCR (General Language Model-Optical Character Recognition)
GLM-OCR merupakan model OCR multimodal untuk pemahaman dokumen kompleks yang dibangun di atas arsitektur encoder-decoder GLM-V (Team dkk., 2026). Arsitektur GLM-V yang mendasari GLM-OCR terdiri dari tiga komponen inti yaitu vision encoder (CogViT), MLP adapter sebagai konektor lintas-modal yang ringan dengan token downsampling yang efisien, dan language decoder berbasis GLM-0.5B (Z.ai, 2026).

Page 32
<page_number>29</page_number>

1. Arsitektur GLM-V
Keluarga model GLM-V (GLM-4.1V-Thinking, GLM-4.5V, dan GLM-4.6V) menggunakan AIMv2-Huge sebagai inisialisasi vision encoder. Untuk memungkinkan ViT (Vision Transformer) mendukung resolusi gambar dan rasio aspek yang arbitrer, dua adaptasi diperkenalkan. Pertama, 2D-RoPE diintegrasikan ke dalam lapisan self-attention ViT, memungkinkan model untuk memproses gambar dengan rasio aspek ekstrem (lebih dari 200:1) atau resolusi tinggi (di atas 4K). Kedua, position embedding absolut yang dapat dipelajari dari ViT pre-trained dipertahahkan dan diadaptasi secara dinamis ke masukan resolusi variabel melalui interpolasi bikubik. Untuk patch masukan pada grid H_p × W_p, koordinat integer g = (w, h) dari setiap patch dinormalisasi ke grid kontinu g_{nr} yang mencakup [-1,1]:

g_{nr} = (w_{norm}, h_{norm}) = 2 · (w + 0.5 / W_p, h + 0.5 / H_p) - 1 (2. 6)

Koordinat yang telah dinormalisasi kemudian digunakan untuk mengambil sampel dari tabel position embedding asli P_{orig} menggunakan fungsi interpolasi bikubik I_bicubic guna menghasilkan embedding posisi yang telah diadaptasi P_{adapted}:

P_{adapted}(g) = I_bicubic(P_{orig}, g_{norm}) (2. 7)

Seperti pada Gambar 2.5 yang menunjukkan arsitektur GLM-V yang terdiri dari tiga komponen yaitu ViT encoder untuk memproses dan mengkodekan gambar dan video, MLP projector untuk menyelaraskan fitur visual ke token tekstual, dan LLM sebagai language decoder untuk memproses token multimodal.

<img>Diagram showing the architecture of GLM-V model. It includes a Language Decoder, a ViT Encoder with native resolution and 2x temporal compression, and an MLP Projector. The diagram also shows input images and videos with their dimensions (e.g., Image 1: Height: 1274, Width: 952), Image 2: Height: 1596, Width: 2548), Video 1: Height: 546, Width: 980). Text labels include "From the given image, ...", "Could you tell me...?", "Time index token", "Predicted token", and "GLM-V" logo.</img> Gambar 2. 5 Arsitektur model GLM-V (diadaptasi dari Team et al., 2025)

Page 33
<page_number>30</page_number>

2. Multi-Token Prediction (MTP)
GLM-OCR memperkenalkan loss Multi-Token Prediction (MTP) untuk meningkatkan efisiensi pelatihan dan akurasi pengenalan. Berbeda dari pemodelan bahasa standar yang mempelajari prediksi next-token dengan objektif cross-entropy L₁ = −Σₜ log Pθ(xₜ₊₁ | xₜ:₁), MTP menggeneralisasi pendekatan ini dengan menginstruksikan model untuk memprediksi n token masa depan secara bersamaan di setiap posisi dalam korpus pelatihan:

Lₙ = −Σₜ log Pθ(xₜ₊ⁿ:ₜ₊₁ | xₜ:₁) (2. 8)

Model ini menggunakan trunk bersama untuk menghasilkan representasi laten zₜ:₁ dari konteks yang diamati xₜ:₁, yang kemudian dimasukkan ke dalam n head keluaran independen untuk memprediksi secara paralel setiap token masa depan:

Pθ(xₜ₊ᵢ | xₜ:₁) = softmax(fᵤ(fₕᵢ(fₛ(xₜ:₁)))) (2. 9) untuk i = 1, ..., n, dengan fₛ adalah Transformer trunk bersama, fₕᵢ adalah lapisan transformer head keluaran ke-i, dan fᵤ adalah matriks unembedding bersama.

Pendekatan MTP mengurangi diskrepansi distribusional antara teacher forcing pada saat pelatihan dan pembangkitan autoregressif pada saat inferensi, serta secara implisit memberikan bobot lebih tinggi pada token-token yang merupakan titik keputusan (choice points) yang berkorelasi erat dengan kelanjutan teks. Eksperimen menunjukkan bahwa model prediksi 4-token memecahkan 12% lebih banyak masalah pada HumanEval dan 17% lebih banyak pada MBPP dibandingkan model next-token yang sebanding, dan inferensi dapat dipercepat hingga 3× melalui self-speculative decoding (Gloeckle dkk., 2024).

3. Reinforcement Learning untuk OCR
GLM-OCR menerapkan reinforcement learning (RL) yang stabil untuk seluruh tugas guna meningkatkan generalisasi. Proses RL menggunakan GRPO (Group Relative Policy Optimization) sebagai algoritma optimisasi dan merancang sistem reward spesifik-domain untuk setiap subdomain multimodal. Untuk domain OCR secara khusus, desain reward menggunakan edit distance yang diformulasikan sebagai:

Page 34
<page_number>31</page_number>

reward({OCR} = 1 - \frac{d{edit}(ans,gt)}{\max(|ans|, |gt|)}) (2. 10)

dengan (d_{edit}(ans,gt)) adalah jarak edit antara jawaban model dan ground truth, (|ans|) dan (|gt|) masing-masing adalah panjang jawaban dan ground truth. Sistem reward yang presisi merupakan kunci efektivitas RLVR (Reinforcement Learning with Verifiable Rewards), dan ketika menskalakan RL ke seluruh domain multimodal, kelemahan dalam sinyal reward untuk satu kapabilitas tunggal dapat mengganggu seluruh pelatihan.

Selain itu, GLM-OCR menggunakan Reinforcement Learning with Curriculum Sampling (RLCS) yang menerapkan wawasan curriculum learning pada pengambilan sampel daring. RLCS menggunakan kurikulum adaptif yang secara kontinu menyesuaikan tingkat kesulitan sampel pelatihan untuk mencocokkan kemampuan model yang terus berkembang, memastikan setiap pembaruan memberikan informasi yang maksimal. Pendekatan ini mendownsample contoh yang terlalu mudah maupun yang saat ini terlalu sulit, dan meningkatkan paparan pada tingkat kesulitan menengah di mana model memperoleh manfaat terbesar.

4. Pipeline Analisis Dokumen
Untuk pemrosesan dokumen end-to-end, GLM-OCR dikombinasikan dengan PP-DocLayoutV3 untuk analisis tata letak dan pengenalan paralel. PP-DocLayoutV3 merupakan evolusi arsitektural signifikan yang bertransisi dari deteksi persegi panjang standar ke kerangka segmentasi instansi yang robust, sambil secara simultan mengintegrasikan prediksi urutan baca (reading order prediction) ke dalam arsitektur Transformer terpadu secara end-to-end (Cui dkk., 2026). Model ini memprediksi mask yang presisi pada tingkat piksel untuk elemen tata letak, yang krusial untuk mengisolasi komponen dokumen dalam skenario non-ideal seperti halaman miring atau melengkung. Urutan baca diturunkan dari skor presedens berpasangan (pairwise precedence score) (S_{i,j}) yang dihitung dari query embedding yang telah diperhalus melalui global pointer mechanism:

(S_{i,j} = \frac{f(q_i, q_j) - f(q_j, q_i)}{\sqrt{d_h}}, \quad \text{di mana } f(q_i, q_j) = (W_q q_i)^T (W_k q_j)) (2. 11)

Page 35
<page_number>32</page_number>

dengan $W_q, W_k \in R^{d_x \times d_h}$ adalah matriks proyeksi yang dapat dipelajari dan $d_h$ menyatakan dimensi tersebunyi. Matriks relasi yang dihasilkan $S \in R^{N \times N}$ bersifat anti-simetris ($S_{i,j} = -S_{j,i}$), di mana $S_{i,j} > 0$ mengimplikasikan elemen i mendahului elemen j. Urutan baca akhir ditentukan melalui strategi Voting-based Ranking yang mengurutkan elemen berdasarkan total suara presedens absolut $V_j = \sum_{i=1, i \neq j}^N \sigma(S_{i,j})$. Seperti yang ditunjukkan Gambar 2.6 arsitektur dari PP-DocLayoutV3 bekerja.

<img>Diagram showing the architecture of PP-DocLayoutV3. It includes sections labeled "Input", "Backbone", "Encoder&Decoder", "Class Head", "Box Head", "Mask Head", "Order Head", "Bounding Box", "Class Postprocess", "Box Postprocess", "Mask Postprocess", "Order Postprocess", "Bounding Box With Order", "Hidden Feature", "Q Projection", "K Projection", "Dot Product", "Logits Matrix", "Relative-Order Logits", and a table with columns for class labels (Background, Class label is paragraph title, order is 2, Class label is figure, Class label is text, order is unknown) and their corresponding bounding box positions.</img>

GAMBAR 2. 6 ARSITEKTUR PP-DOCAYOUTV3 (DIADAPTASI DARI CUI DKK., 2026)

Performa dan Keunggulan
GLM-OCR mencapai skor 94,62 pada OmniDocBench V1.5, menempati peringkat pertama secara keseluruhan, dan memberikan hasil state-of-the-art pada benchmark pemahaman dokumen utama, termasuk pengenalan rumus, pengenalan tabel, dan ekstraksi informasi. Dengan hanya 0,9 miliar parameter, GLM-OCR mendukung deployment melalui vLLM, SGLang, dan Ollama, secara signifikan mengurangi latensi inferensi dan biaya komputasi, menjadikannya ideal untuk layanan high-concurrency dan deployment di perangkat edge.

Model ini mendukung dua jenis skenario prompt yaitu pemrosesan dokumen (document parsing) untuk mengekstraksi konten mentah dengan tugas pengenalan teks, rumus, dan tabel, serta ekstraksi informasi (information extraction) untuk mengekstraksi informasi terstruktur dari dokumen sesuai skema JSON yang didefinisikan.

Page 36
<page_number>33</page_number>

Tabel 2. 1 Perbandingan model dalam parsing dokumen & ekstraksi informasi

Benchmark	GLM-OCR	PaddleOCR-VL-1.5	Deepseek-OCR2	MinerU2.5	dots.ocr	Gemini-3-Pro	GPT-5.2
OmniDocBench v1.5	94,6	94,5	91,1	90,7	88,4	90,3	85,4
OCRBench (Text)	94,0	75,3	34,7	75,3	92,1	91,9	83,7
UniMERNet	96,5	96,1	85,8	96,4	90,0	96,4	90,5
PubTabNet	85,2	84,6	-	88,4	71,0	91,4	84,4
TEDS_TEST	86,0	83,3	-	85,4	62,4	81,8	67,6
Nanonets-KIE	93,7	-	-	-	-	95,2	87,5
Handwritten-Forms	86,1	-	-	-	-	94,5	78,2
Sumber: (Z.ai, 2026)

Keterangan: Specialized VLM: GLM-OCR, PaddleOCR-VL-1.5, Deepseek-OCR2, MinerU2.5, dots.ocr. General VLM: Gemini-3-Pro, GPT-5.2.

Tabel 2. 2 Perbandingan model dalam skenario dunia nyata

Task	GLM-OCR	PaddleOCR-VL-1.5	Deepseek-OCR2	MinerU2.5	dots.ocr	Gemini-3-Pro	GPT-5.2
Code	84,7	75,8	82,1	82,9	80,8	86,9	84,4
Real-world Table	91,5	86,1	-	70,8	81,8	90,6	86,7
Handwriting	87,0	87,4	73,8	54,2	71,7	90,0	78,0
Multi-language	69,3	54,8	56,1	27,8	65,1	86,2	70,1
Seal	90,5	42,2	40,4	-	63,0	91,3	58,8
Receipt (KIE)	94,5	-	-	-	-	97,3	83,5
Page 37
<page_number>34</page_number>

Sumber: (Z.ai, 2026)

Keterangan: Specialized VLM: GLM-OCR, PaddleOCR-VL-1.5, Deepseek-OCR2, MinerU2.5, dots.ocr. General VLM: Gemini-3-Pro, GPT-5.2.

Tabel 2. 3Perbandingan model dalam kecepatan inferensi

Methods	Image Inputs (Pages / Sec)	PDF Inputs (Pages / Sec)
GLM-OCR	0,67	1,86
PaddleOCR-VL-1.5	0,39	1,22
Deepseek-OCR2	0,32	–
MinerU2.5	0,18	0,48
dots.ocr	0,10	–
Sumber: (Z.ai, 2026)

Keterangan: Specialized VLM: GLM-OCR, PaddleOCR-VL-1.5, Deepseek-OCR2, MinerU2.5, dots.ocr.

Pada percobaan awal penelitian ini, GLM-OCR tanpa fine-tuning menunjukkan kemampuan ekstraksi teks yang memadai namun belum konsisten dalam mengikuti skema JSON yang telah didefinisikan. Model cenderung menggunakan nama field yang berbeda dari spesifikasi, menghilangkan field yang tidak terisi alih-alih mengisinya dengan nilai kosong, dan menghasilkan struktur JSON yang tidak sepenuhnya konsisten antar inferensi. Melalui proses IFT dengan LoRA menggunakan LLaMA Factory, model diadaptasi untuk menghasilkan output yang sesuai dengan ekstrasi skema yang telah ditetapkan.

2.9 Key Information Extraction
Key Information Extraction (KIE) merupakan subbidang dari visual document understanding yang merujuk pada tugas untuk mengekstrak informasi spesifik dan terstruktur dari dokumen semi-structured (Rombach dan Fettke, 2026). Pada dokumen visually-rich seperti struk pembelian, faktur, dan formulir bisnis, KIE menghadapi tantangan yang unik karena informasi tidak hanya terkandung dalam konten teks tetapi juga dalam tata letak visual dokumen secara keseluruhan (Huang dkk., 2019).

Page 38
<page_number>35</page_number>

Dokumen struk pembelian termasuk dalam kategori Visually-Rich Document Understanding (VRDU) yang membutuhkan pemahaman terpadu antara konten tekstual dan struktur spasial dua dimensi (Z. Wang dkk., 2023). Pada kategori ini, posisi elemen teks dalam ruang dokumen membawa makna semantik yang setara pentingnya dengan konten teks itu sendiri (Xu dkk., 2020). Sebagai contoh, nilai numerik yang berada di kolom kanan sejajar dengan nama item merupakan harga item tersebut, sementara nilai numerik di baris terbawah dokumen dengan format yang berbeda merupakan grand total pembayaran.

Pendekatan berbasis VLM untuk KIE yang digunakan dalam penelitian ini memanfaatkan kemampuan model untuk memahami hubungan spasial dan semantik secara simultan dalam satu inferensi. Dengan memberikan gambar dokumen dan skema JSON target sebagai instruksi, model secara langsung menghasilkan output terstruktur tanpa memerlukan tahapan segmentasi dokumen atau pemrosesan pipeline yang terpisah-pisah.

2.10 Agentic AI
Agentic AI merupakan sebuah paradigma baru dalam kecerdasan buatan yang mengacu pada sistem otonom yang dirancang untuk mencapai tujuan-tujuan kompleks dengan intervensi manusia yang minimal. Berbeda dengan AI tradisional yang bergantung pada instruksi terstruktur dan pengawasan ketat, Agentic AI mendemonstrasikan kemampuan adaptasi, pengambilan keputusan tingkat lanjut, dan kemandirian operasional, sehingga memungkinkannya beroperasi secara dinamis dalam lingkungan yang terus berkembang. Era Agentic AI (2022–sekarang) merupakan era terkini di mana kemampuan generatif LLM dimanfaatkan untuk aksi dan otonomi, ditandai dengan kemunculan AI Agent seperti AutoGPT yang dapat mengejar tujuan melalui perencanaan dan penggunaan alat (tool use), yang kemudian berkembang menjadi sistem multi-agen yang lebih kompleks (Abou Ali, Dornaika dan Charafeddine, 2025).

2.10.1 AI Agent
AI Agent merupakan sistem berbasis LLM yang dilengkapi dengan kemampuan untuk merencanakan, memutuskan, dan mengeksekusi serangkaian

Page 39
<page_number>36</page_number>

tindakan secara otonom untuk mencapai tujuan yang ditetapkan (L. Wang dkk., 2023). Berbeda dengan penggunaan LLM sebagai komponen reaktif, AI agent bersifat proaktif dalam berinteraksi dengan lingkungan eksternal secara iteratif (Xi dkk., 2023).

Menurut Sapkota dkk., 2026, AI Agent dapat dibedakan dari Agentic AI melalui karakteristik berikut: AI agent merupakan sistem modular yang didorong dan diaktifkan oleh LLM untuk otomatisasi tugas spesifik, dengan kemampuan melakukan tool integration, prompt engineering, dan peningkatan reasoning. Sementara itu, Agentic AI merepresentasikan perggeseran paradigma yang ditandai oleh kolaborasi multi-agen, dekomposisi tugas dinamis, memori persisten, dan otonomi yang terkoordinasi.

Komponen utama AI Agent terdiri dari empat elemen fungsional. Elemen pertama adalah profil yang mendefinisikan peran, kemampuan, dan batasan agent. Elemen kedua adalah memori yang menyimpan konteks percakapan dan informasi sesi. Elemen ketiga adalah perencanaan yang memungkinkan agent mendekomposisi tugas kompleks menjadi langkah-langkah yang dapat dieksekusi secara berurutan. Elemen keempat adalah aksi yang memungkinkan agent berinteraksi dengan lingkungan eksternal melalui pemanggilan tool yang terdefinisi (Acharya, Kuppan dan Divya, 2025).

Dalam penelitian ini, AI Agent diimplementasikan sebagai Supervisor Agent bernama Klaudia yang bertugas memahami permintaan pengguna, mengorkestrasikan alur kerja pemrosesan struk, dan mendelegasikan tugas ke sub-agent yang sesuai berdasarkan kebutuhan pada setiap giliran percakapan.

2.10.2 Multi Agent System (MAS)
Multi-Agent System (MAS) merupakan arsitektur yang terdiri dari beberapa AI Agent yang berkolaborasi untuk menyelesaikan tugas kompleks yang tidak efisien atau tidak praktis apabila diselesaikan oleh satu agent tunggal. Setiap agent dalam MAS memiliki spesialisasi, konteks sistem, dan himpunan tool yang berbeda, dan berinteraksi melalui mekanisme komunikasi yang terdefinisi (Gao dkk., 2025).

Page 40
<page_number>37</page_number>

Keunggulan utama MAS dibandingkan pendekatan single-agent adalah kemampuan untuk menerapkan prinsip separation of concerns, di mana setiap agent dapat difokuskan pada domain yang spesifik sehingga kompleksitas sistem dapat dikelola dengan lebih baik (Biswas dkk., 2025). Keunggulan MAS atas sistem single-agent telah terdokumentasi secara empiris, di mana sistem multi-agent menunjukkan rata-rata peningkatan performa sebesar 21,3% dibandingkan model foundation tunggal, dengan peningkatan terbesar pada domain yang memerlukan penalaran logis langkah-demi-langkah (31,7%) dan analisis multi-perspektif (28,4%). Selain itu, pendekatan kolaboratif menggunakan critic dan refinement agents mencapai peningkatan 26% dalam akurasi pengambilan fakta sekaligus mengurangi halusinasi sebesar 41% dibandingkan pendekatan single-agent tradisional (Mohan Singh, 2025). Studi (Sreedhar dan Chilton, 2024) secara khusus mengungkapkan bahwa sistem multi-agent lebih akurat daripada LLM tunggal (88% vs. 50%) dalam mensimulasikan penalaran dan aksi manusia untuk pasangan kepribadian tertentu. Dalam eksperimen pada ultimatum game, sistem multi-agent mencapai gameplay yang konsisten dengan data eksperimental manusia dalam 85% simulasi, sementara LLM tunggal hanya mencapai 50%.

Dalam penelitian ini, MAS diimplementasikan dengan pembagian tanggung jawab yang jelas antara Supervisor Agent untuk orkestrasi dan percakapan, SQL Agent untuk operasi pembacaan database, dan Data Entry Team yang terdiri dari agen-agen yang bertugas membaca, memodifikasi, dan menulis ke Google Sheets.

2.10.3 Hierarchical Agent Teams

Hierarchical Agent Teams (tim agen hierarkis) merupakan pola arsitektur MAS di mana agent-agent diorganisasi dalam struktur hierarkis dengan Supervisor Agent yang mengkoordinasikan pekerjaan sub-agent yang lebih terspesialisasi. Pendekatan ini terinspirasi dari cara seorang konduktor mengorkestrasi simfoni, di mana planning agent pusat mengurai tujuan kompleks dan mendelegasikan sub-tugas kepada tim agent spesialis (Zhang dkk., 2026). Pola ini diimplementasikan menggunakan LangGraph, yaitu framework ekstensi dari LangChain yang memungkinkan pembuatan alur agent sebagai state machine yang dapat dikontrol secara deterministik. Pada Gambar 2.7 menunjukkan contoh implementasi

Page 41
<page_number>38</page_number>

Hierarchical Agent Teams dengan planning agent sebagai orchestrator dan specialized sub-agents.

<img>A diagram titled "AgentOrchestra" illustrating Hierarchical Role-based Cooperation. It shows a Planner at the top, which receives a Task. The Planner then assigns this task to three sub-agents: Researcher, Browser, and Analyzer. Each sub-agent can further delegate tasks to other sub-agents (e.g., sub-agent A, B, C). The Planner also handles feedback loops from these sub-agents. The diagram includes sections labeled "Planning Agent", "Tools", "User Objectives", and "Deep Researcher Agent", "Browser Use Agent", "Deep Analyzer Agent", and "Other Sub-Agent".</img>

Gambar 2.7 Contoh arsitektur hierarchical agent teams (diadaptasi dari W. Zhang dkk., 2026)

Dibandingkan dengan arsitektur flat (non-hierarkis), tim agent hierarkis menawarkan keunggulan struktural berupa kemampuan dekomposisi tugas yang lebih efisien karena planning agent memiliki perspektif global, spesialisasi yang lebih tajam karena setiap sub-agent dioptimalkan untuk domain tertentu, serta skalabilitas yang lebih baik karena penambahan kapabilitas baru cukup dilakukan dengan menambahkan sub-agent baru tanpa mengubah arsitektur inti.

Dalam pola ini, supervisor atau sebagai planing agent menerima permintaan dari pengguna, mengevaluasi kebutuhan tugas, dan mendelegasikan pekerjaan ke sub-agent yang paling sesuai. Sub-agent mengeksekusi tugas spesifik menggunakan tools yang tersedia, mengembalikan hasilnya ke supervisor, yang kemudian mengintegrasikan hasil tersebut dan merespons pengguna dengan informasi yang komprehensif.

LangGraph digunakan untuk mendefinisikan state graph yang merepresentasikan alur percakapan dan eksekusi tugas sebagai sebuah graf terarah. Node dalam graf merepresentasikan agent atau proses tertentu, sementara edge merepresentasikan transisi kondisional berdasarkan output agent. Mekanisme interrupt bawaan LangGraph memungkinkan implementasi human-in-the-loop

Page 42
<page_number>39</page_number>

pada titik-titik kritis dalam alur eksekusi yang membutuhkan konfirmasi manusia sebelum tindakan irreversible dilakukan (LangChain, 2026).

2.11 HITL (Human in the Loop)

Human-in-the-Loop (HITL) merupakan paradigma sistem AI di mana manusia dilibatkan secara aktif dalam proses pengambilan keputusan sistem, terutama pada titik-titik kritis yang membutuhkan validasi, koreksi, atau persetujuan eksplisit sebelum sistem melanjutkan ke tahap berikutnya (Natarajan dkk., 2024).

Dalam konteks sistem agentic berbasis LLM, HITL sangat relevan untuk menangani skenario di mana output model bersifat non-deterministik, terdapat ambiguitas dalam instruksi pengguna, atau tindakan yang akan dieksekusi bersifat irreversible (Atil dkk., 2025). Penulisan data ke database atau spreadsheet adalah contoh operasi irreversible yang apabila dilakukan berdasarkan ekstraksi yang salah akan menghasilkan data corruption yang sulit diperbaiki. Keterlibatan manusia di titik-titik ini secara langsung mengurangi risiko silent data corruption yang tidak terdeteksi.

Implementasi HITL dalam LangGraph dilakukan melalui mekanisme interrupt yang memungkinkan eksekusi graf dihentikan sementara pada node tertentu untuk menunggu konfirmasi atau input koreksi dari pengguna. Setelah pengguna memberikan respons, eksekusi dilanjutkan dari titik yang sama dengan membawa informasi tambahan dari pengguna sebagai bagian dari konteks state yang diperbarui. Pada Gambar 2.8 menunjukkan skema arsitektur penerapan HITL pada agentic AI.

Page 43
<page_number>40</page_number>

flowchart TD
    A[Agent] --> B{Interrupt?}
    B -- yes --> C{Human}
    B -- no --> D[Execute]
    C -- approve --> D
    C -- edit --> D
    C -- reject --> E[Cancel]
    D --> A
Gambar 2. 8 Arsitektur HITL pada sistem Agentic AI berbasis LangGraph
(diadaptasi dari LangChain, 2026)

Dalam penelitian ini, HITL diimplementasikan sebagai checkpoint konfirmasi sebelum operasi penulisan data ke Google Sheets dieksekusi. Setelah Supervisor Agent memverifikasi data hasil ekstraksi bersama pengguna, pengguna diberikan kesempatan untuk meninjau, mengkonfirmasi, atau mengoreksi data sebelum Data Entry Team menjalankan operasi penulisan melalui MCP-GSheets. Keunggulan kritis HITL dalam konteks data entry adalah kemampuannya untuk mengatasi hallucination dan ambiguitas yang mungkin terjadi ketika agent memproses dokumen dengan kualitas rendah atau format yang tidak lazim. Alih-alih membiarkan agent secara otonom memasukkan data yang berpotensi salah ke dalam sistem, mekanisme HITL menyediakan checkpoint terstruktur di mana pengguna dapat mengonfirmasi, memodifikasi, atau menolak hasil ekstraksi sebelum aksi final dieksekusi.

2.12 MCP (Model Context Protocol)
Model Context Protocol (MCP) merupakan standar terbuka yang mendefinisikan protokol komunikasi dua arah yang terpadu dan dynamic discovery antara model AI dengan alat atau sumber daya eksternal, yang bertujuan untuk meningkatkan interoperabilitas dan mengurangi fragmentasi di berbagai sistem. MCP diperkenalkan oleh Anthropic pada akhir tahun 2024, terinspirasi dari Language Server Protocol (LSP), sebagai solusi atas fragmentasi yang terjadi

Page 44
<page_number>41</page_number>

dalam ekosistem integrasi tool pada aplikasi AI. MCP mendefinisikan antarmuka yang konsisten antara AI model sebagai client dan layanan eksternal sebagai server, sehingga integrasi antara model dengan berbagai kapabilitas eksternal dapat dilakukan secara modular, dapat dipertukarkan, dan tidak bergantung pada implementasi spesifik model tertentu (Hou dkk., 2025).

Arsitektur MCP terdiri dari tiga komponen utama. Komponen pertama adalah MCP Host, yaitu aplikasi yang menjalankan AI model dan mengelola komunikasi dengan MCP Server. Komponen kedua adalah MCP Client, yaitu modul dalam host yang mengelola koneksi dan protokol komunikasi ke server. Komponen ketiga adalah MCP Server, yaitu layanan yang mengekspos kapabilitas berupa tools, resources, dan prompts melalui antarmuka MCP yang terstandarkan.

Keunggulan utama penggunaan MCP dibandingkan integrasi tool secara langsung adalah pemisahan yang tegas antara logika AI (reasoning) dan eksekusi tool (action). Dalam prinsip “agent sebagai reasoning, tool sebagai execution”, MCP menjadi batas eksplisit yang memastikan seluruh operasi pada sumber data eksternal selalu melalui tool yang terdefinisi dengan kontrak yang jelas dan dapat diaudit, bukan melalui eksekusi kode arbitrer yang dihasilkan oleh model (Oribe, 2025).

Dalam penelitian ini, dua MCP Server diimplementasikan. MCP-SQLite menyediakan tool untuk operasi pembacaan database SQLite yang digunakan oleh SQL Agent untuk mengambil data dokumen, halaman, dan hasil ekstraksi. MCP-GSheets menyediakan tool untuk operasi pembacaan dan penulisan ke Google Sheets yang digunakan oleh Data Entry Team untuk membuat sheet, memperbarui sel, dan menambahkan baris data.

2.13 Prompt Engineering
Prompt engineering merupakan teknik yang tidak terpisahkan untuk memperluas kapabilitas LLM dan VLM melalui perancangan instruksi tugas-spesifik, yang dikenal sebagai prompt, untuk meningkatkan efektivitas model tanpa memodifikasi parameter inti model tersebut. Alih-alih memperbarui parameter model, prompt memungkinkan integrasi yang mulus dari model pre-trained ke

Page 45
<page_number>42</page_number>

dalam tugas-tugas downstream dengan hanya mengandalkan prompt yang diberikan untuk membangkitkan perilaku model yang diinginkan (Sahoo dkk., 2025).

Signifikansi prompt engineering terletak pada dampak transformatifnya terhadap adaptabilitas LLM dan VLM. Berbeda dengan paradigma tradisional di mana pelatihan ulang model atau fine-tuning ekstensif sering kali diperlukan untuk performa yang spesifik-tugas, prompt engineering memungkinkan model yang sama untuk menjalankan beragam tugas melalui desain instruksi yang cermat. Lanskap prompt engineering kontemporer mencakup spektrum teknik yang luas, mulai dari metode foundational seperti zero-shot dan few-shot prompting hingga pendekatan yang lebih kompleks seperti chain of thought dan ReAct prompting.

2.13.1 Zero Shot Prompting
Zero-shot prompting adalah teknik di mana model diberikan instruksi dan deskripsi tugas tanpa contoh eksplisit dalam prompt. Model mengandalkan pengetahuan dan kemampuan generalisasi yang diperoleh selama pre-training untuk memahami dan menyelesaikan tugas yang diminta. Dalam penelitian ini, zero-shot prompting diterapkan pada prompt GLM-OCR yang memberikan skema JSON target dan meminta model mengekstrak informasi dari gambar struk sesuai skema tersebut tanpa contoh referensi tambahan dalam prompt.

2.13.2 Few Shot Prompting
Few-shot prompting adalah teknik di mana model diberikan sejumlah kecil contoh pasangan input-output dalam prompt sebelum tugas yang sebenarnya diberikan. Contoh-contoh ini memberikan panduan kontekstual tentang format, gaya, dan kualitas output yang diharapkan. Dalam penelitian ini, few-shot prompting diterapkan pada system prompt agent untuk mendefinisikan pola respons dan format yang diinginkan dari Supervisor Agent dalam berinteraksi dengan pengguna.

2.13.3 Chain of Thought Prompting
Chain-of-Thought (CoT) prompting adalah teknik yang mendorong model untuk menghasilkan langkah-langkah penalaran eksplisit secara berurutan sebelum

Page 46
<page_number>43</page_number>

memberikan jawaban atau tindakan akhir. CoT terbukti secara signifikan meningkatkan performa model pada tugas yang membutuhkan penalaran multi-langkah (Weidkk., 2023). Dalam sistem ini, CoT diterapkan pada Supervisor Agent untuk memastikan proses analisis kebutuhan pengguna dan penentuan tindakan yang tepat dilakukan secara sistematis sebelum delegasi ke sub-agent dieksekusi.

2.13.4 ReAct Prompting

ReAct (Reasoning and Acting) adalah framework yang mengintegrasikan kemampuan penalaran (CoT) dengan kemampuan bertindak melalui penggunaan tool dalam satu alur inferensi yang terpadu (Yao dkk., 2023). Dalam framework ReAct, model beriterasi melalui siklus thought yang berisi penalaran tentang situasi saat ini, action yang berisi pemanggilan tool yang dipilih, dan observation yang berisi pemrosesan hasil tool untuk menentukan langkah selanjutnya. Siklus ini berulang hingga tugas dinyatakan selesai.

ReAct menjadi paradigma utama dalam implementasi seluruh agent pada penelitian ini. Setiap agent dalam sistem mengikuti siklus ReAct di mana model terlebih dahulu menganalisis konteks dan kebutuhan (thought), kemudian memilih dan memanggil tool yang sesuai melalui MCP (action), lalu memproses hasil tool untuk menentukan apakah tugas sudah selesai atau diperlukan langkah tambahan (observation).

2.13.5 Persona-based Prompting

Persona-based prompting atau role-play prompting adalah teknik perancangan instruksi yang menetapkan identitas, karakter, atau peran spesifik kepada model bahasa untuk mengatur nada bicara, perilaku, dan batasan operasionalnya. Menurut (Shanahan, McDonell dan Reynolds, 2023), pemberian persona memungkinkan model untuk mengadopsi kerangka berpikir tertentu yang konsisten, di mana model tidak hanya memproses informasi secara fungsional tetapi juga menyesuaikan gaya komunikasinya dengan profil yang diberikan. Teknik ini bekerja dengan cara membatasi ruang probabilitas respons model agar selaras dengan karakteristik sosiolinguistik dan kepakaran yang melekat pada peran tersebut, sehingga meningkatkan kepercayaan pengguna dan kejelasan interaksi.

Page 47
<page_number>44</page_number>

Dalam penelitian ini, persona-based prompting diimplementasikan untuk membentuk identitas "Klaudia" sebagai asisten AI yang ahli dalam pemrosesan data struk belanja. Penggunaan persona ini berfungsi sebagai jangkar perilaku (behavioral anchor) yang memastikan agen tetap beroperasi dalam batas kapabilitasnya, seperti membedakan antara alur data otomatis ke database dan kebutuhan instruksi eksplisit untuk penginputan ke Google Sheets. Melalui pendefinisian persona yang ramah, efisien, dan proaktif, agen mampu memberikan ringkasan hasil pemrosesan serta klarifikasi permintaan ambigu dengan nada profesional, yang secara efektif menjembatani kesenjangan antara fungsi teknis ekstraksi data dan kebutuhan komunikasi pengguna yang intuitif.

2.14 Context Engineering
Context engineering adalah praktik merancang dan mengelola secara sistematis seluruh konteks yang disuplai ke LLM pada setiap giliran inferensi, dengan tujuan memaksimalkan relevansi, akurasi, dan konsistensi respons model. Berbeda dengan prompt engineering yang fokus pada perancangan instruksi tunggal, context engineering mencakup pengelolaan komprehensif seluruh informasi yang membentuk jendela konteks model, termasuk instruksi sistem, riwayat percakapan, hasil tool, dan informasi sesi yang relevan (Mei dkk., 2025).

Komponen konteks yang dikelola dalam penelitian ini mencakup instruksi persona dan kapabilitas Klaudia dalam system prompt, riwayat percakapan sesi yang diambil dari database untuk memberikan memori percakapan, informasi file yang telah diunggah dalam sesi aktif beserta status ekstraktornya, dan hasil observasi dari pemanggilan tool oleh sub-agent yang dikembalikan ke supervisor.

Implementasi context enrichment dalam penelitian ini dilakukan dengan menginjeksikan informasi tentang semua file aktif dalam sesi ke dalam system prompt Supervisor Agent pada setiap giliran percakapan. Informasi ini mencakup nama file, tipe dokumen, status ekstraksi, jumlah halaman, dan file ID yang dapat direferensikan oleh agent. Mekanisme ini memastikan Supervisor Agent selalu memiliki kesadaran penuh tentang konteks sesi saat ini tanpa perlu melakukan query database secara eksplisit pada setiap giliran.

Page 48
<page_number>45</page_number>

2.15 Benchmark Agentic AI
Evaluasi performa sistem Agentic AI memerlukan benchmark yang mampu mengukur kemampuan-kemampuan khas yang membedakannya dari model bahasa konvensional, meliputi kemampuan penggunaan tool (tool use), perencanaan multi-langkah, penalaran jangka panjang (long-horizon reasoning), kolaborasi antar-agent, dan kemampuan untuk mempertahankan koherensi dalam konteks yang sangat panjang. Lanskap benchmark Agentic AI telah berevolusi dari pengujian pengetahuan berbasis pertanyaan tetap, menuju paradigma evaluasi yang interaktif dan dinamis yang mengukur kemampuan agentic secara lebih realistis.

2.15.1 τ²-Bench
τ²-Bench (Tau-Squared Bench) merupakan benchmark yang dirancang untuk mengevaluasi conversational AI agents dalam lingkungan dual-control, di mana baik agent AI maupun pengguna dapat menggunakan tool untuk berinteraksi dengan dunia bersama yang dinamis. Berbeda dengan benchmark konvensional yang mensimulasikan lingkungan single-control (di mana hanya agent AI yang dapat menggunakan tool sementara pengguna tetap sebagai penyedia informasi pasif), τ²-Bench mencerminkan skenario dunia nyata seperti dukungan teknis di mana pengguna perlu aktif berpartisipasi dalam memodifikasi state lingkungan bersama (Barres dkk., 2025).

Eksperimen pada τ²-Bench menunjukkan penurunan performa yang signifikan ketika agent beralih dari lingkungan tanpa-pengguna ke lingkungan dual-control, menyoroti tantangan dalam memandu aksi pengguna sebagai salah satu aspek yang paling menantang bagi sistem agent percakapan saat ini.

2.15.2 MCP-Atlas
MCP-Atlas adalah benchmark berskala besar untuk mengevaluasi kompetensi penggunaan tool (tool-use competency) dengan MCP server nyata, terdiri dari 36 MCP server nyata dan 220 tool yang mencakup 1.000 tugas yang dirancang untuk menilai kompetensi penggunaan tool dalam workflow multi-langkah yang realistis. MCP-Atlas mengatasi ketegangan yang persisten dalam

Page 49
<page_number>46</page_number>

benchmark MCP sebelumnya antara ketelitian evaluasi dan skalabilitas melalui tiga pilihan desain utama (Bandi dkk., 2026).

Setiap tugas dalam MCP-Atlas didefinisikan oleh empat komponen wajib yaitu berupa tool set configuration (subset terkontrol 10–25 tool yang diekspos ke agent per tugas, terdiri dari 3–7 target tool dan 5–10 distractor), prompt (permintaan bahasa alami single-turn yang memerlukan beberapa panggilan tool tanpa menyebutkan nama server atau tool secara eksplisit), reference trajectory (urutan minimal panggilan tool yang menyelesaikan tugas, digunakan untuk analisis diagnostik), dan claims list (sekumpulan klaim atomik yang dapat diverifikasi secara independen yang bersama-sama membentuk respons komprehensif). Hasil evaluasi pada model-model frontier mengungkapkan bahwa model terbaik mencapai tingkat kelulusan lebih dari 50%, dengan kegagalan utama terjadi pada tool usage (pemilihan server yang salah, kesalahan parameter, kesalahan urutan) dan task understanding (penghentian dini, sub-tujuan yang terlewat).

2.15.3 APEX-Agents
APEX-Agents (AI Productivity Index for Agents) adalah benchmark untuk menilai apakah AI Agent dapat mengeksekusi tugas lintas-aplikasi jangka panjang (long-horizon, cross-application tasks) yang dibuat oleh analis perbankan investasi, konsultan manajemen, dan pengacara korporat. APEX-Agents mensimulasikan lingkungan kerja nyata di mana agent harus menavigasi file dan tool yang realistis, dengan tugas-tugas yang rata-rata memerlukan 1–2 jam untuk diselesaikan oleh profesional berpengalaman (Vidgen dkk., 2026).

Pembangunan APEX-Agents dilakukan dalam tiga langkah utama. Pertama, tim profesional industri membuat dunia-dunia (worlds) yang kaya data, masing-masing berdasarkan skenario proyek unik, di mana mereka merencanakan pekerjaan, melakukan riset, dan menghasilkan deliverable berkualitas tinggi dari awal. Kedua, profesional membuat tugas-tugas yang realistis dan menantang menggunakan file-file dari dalam setiap dunia. Ketiga, agent diberikan akses ke setiap dunia untuk mengeksekusi tugas-tugas tersebut dengan semua data dan perangkat lunak yang sama dengan yang digunakan manusia.

Page 50
<page_number>47</page_number>

APEX-Agents sangat relevan untuk mengevaluasi Supervisor Agent dalam konteks penelitian ini, yakni agent yang harus mengelola keseluruhan alur dari pembacaan OCR hingga finalisasi data ke dalam spreadsheet tanpa kehilangan fokus sepanjang proses. Benchmark ini cocok digunakan ketika ingin menguji apakah AI benar-benar siap untuk menggantikan atau membantu pekerjaan kantor yang memerlukan pemikiran kritis dan penalaran jangka panjang.

2.15.4 MRCR v2

MRCR v2 (Multi-Round Co-reference Resolution version 2) adalah benchmark evaluasi kemampuan long-context yang melampaui tugas retrieval sederhana, menguji kemampuan model untuk mensintesis beberapa bagian informasi yang tersebar di seluruh konteks secara berurutan dan koheren. Evaluasi ini merupakan bagian dari kerangka Michelangelo yang menggunakan Latent Structure Queries (LSQ) untuk menghasilkan evaluasi penalaran konteks panjang yang dapat diperluas secara arbitrer (Vodrahalli dkk., 2024).

Dalam tugas MRCR, model melihat percakapan panjang antara pengguna dan model, di mana pengguna meminta penulisan (misalnya puisi, teka-teki, esai) tentang topik-topik yang berbeda dan model memberikan respons. Tugas yang diberikan adalah mereproduksi output dari percakapan tersebut yang dihasilkan dari salah satu permintaan spesifik, di mana format atau topik atau keduanya, saling tumpang tindih untuk menciptakan kunci yang secara adversarial mirip satu sama lain. Model dinilai menggunakan metrik string-similarity antara output model dan respons yang benar.

MRCR dapat dipandang sebagai perluasan tugas needle-in-a-haystack (pencarian informasi spesifik dalam dokumen panjang) ke skenario di luar retrieval, yang mengharuskan model menggunakan informasi tentang urutan beberapa "jarum" yang ditempatkan dalam "tumpukan jerami" untuk menjawab kueri. Setup ini memiliki keunggulan menciptakan jarum-jarum yang sangat mirip (highly similar needles) yang harus diambil, sehingga mengharuskan model untuk menggunakan informasi dari dua tempat dalam konteks untuk menentukan jawaban yang benar.

Page 51
<page_number>48</page_number>

2.15.5 Komparasi Performa Model Berdasarkan Benchmark
Evaluasi komprehensif berbagai model frontier pada benchmark Agentic AI memberikan gambaran yang jelas tentang kemampuan dan keterbatasan sistem-sistem terbaik saat ini. (Google DeepMind, 2026) mempublikasikan hasil evaluasi Gemini 3.1 Pro yang mencakup beberapa benchmark utama Agentic AI yang telah dibahas sebelumnya. Tabel 2.15 menyajikan komparasi performa model-model frontier terkemuka pada benchmark-benchmark tersebut.

Tabel 2. 4 Komparasi performa model-model frontier pada benchmark

Agentic AI utama

Benchmark	Gemini 3.1 Pro	Gemini 3 Pro	Sonnet 4.6	Opus 4.6	GPT-5.2
$\tau^2$-Bench
(Retail)	90,8%	85,3%	91,7%	91,9%	82,0%
$\tau^2$-Bench
(Telecom)	99,3%	98,0%	97,9%	99,3%	98,7%
MCP-Atlas	69,2%	54,1%	59,5%	59,5%	60,6%
APEX-Agents (Long Horizon)	33,5%	18,4%	—	29,8%	23,0%
MRCR v2 (8-needle)	84,9%	77,0%	84,9%	84,0%	83,8%
Sumber: (Google DeepMind, 2026)

Hasil komparasi ini mengungkapkan beberapa pola penting. Pertama, pada benchmark $\tau^2$-bench domain telecom, hampir semua model frontier mencapai performa yang tinggi (di atas 97%), mengindikasikan bahwa sistem percakapan dengan kontrol ganda (dual-control) mulai dapat ditangani dengan baik oleh model terkini. Kedua, pada benchmark MCP-Atlas yang menguji kemampuan penggunaan tool yang realistis, masih terdapat disparitas yang signifikan antar model (kisaran 54–69%), menunjukkan bahwa kemampuan multi-tool orchestration masih menjadi tantangan terbuka. Ketiga, pada APEX-Agents yang mengevaluasi tugas-tugas profesional jangka panjang, bahkan model terbaik (Gemini 3.1 Pro) hanya

Page 52
<page_number>49</page_number>

mencapai 33,5%, mengindikasikan masih terdapat kesenjangan yang signifikan antara kemampuan AI dan pelaksanaan pekerjaan profesional yang kompleks secara otonom.

Dalam konteks penelitian ini, benchmark-benchmark tersebut memberikan landasan untuk mengevaluasi performa sistem Agentic AI yang dibangun, khususnya kemampuan penggunaan MCP tool (τ²-Bench dan MCP-Atlas), kemampuan menangani workflow multi-langkah jangka panjang (APEX-Agents), dan kemampuan mempertahankan koherensi konteks selama proses data entry (MRCR v2). Pemilihan model LLM yang tepat dapat mempertimbangkan trade-off antara kemampuan agentic, latensi, dan biaya, menjadi keputusan arsitektural kritis yang harus diinformasikan oleh data benchmark tersebut.

2.16 Guardrails
Seiring dengan meningkatnya integrasi LLM dalam berbagai aplikasi sehari-hari, kebutuhan untuk mengidentifikasi dan memitigasi risiko yang ditimbulkannya menjadi semakin kritis, terutama ketika risiko tersebut dapat memberikan dampak mendalam bagi pengguna dan masyarakat luas. Sebagai respons terhadap tantangan ini, guardrails telah muncul sebagai teknologi pengamanan inti yang bertugas memfilter masukan atau keluaran dari LLM. Menurut (Dong dkk., 2024), guardrail didefinisikan sebagai suatu algoritma yang menerima sekumpulan objek sebagai masukan, seperti masukan dan/atau keluaran dari LLM, kemudian menentukan apakah dan bagaimana tindakan penegakan tertentu dapat diambil guna mengurangi risiko yang terkandung dalam objek-objek tersebut. Sebagai contoh, apabila masukan kepada LLM berkaitan dengan eksploitasi anak, guardrail dapat menghentikan masukan tersebut agar tidak diproses oleh LLM atau mengadaptasi keluarannya sehingga menjadi tidak berbahaya.

Dalam konteks penelitian ini, guardrails diimplementasikan sebagai lapisan perlindungan pertama dalam arsitektur sistem sebelum permintaan pengguna diproses oleh supervisor agent. Lapisan guardrails terdiri dari dua komponen utama yang berjalan secara paralel, yaitu komponen deteksi prompt injection dan

Page 53
<page_number>50</page_number>

jailbreaking menggunakan model klasifikasi khusus, serta komponen blacklist domain menggunakan pendekatan LLM as judge untuk menyaring topik-topik yang berada di luar cakupan sistem.

2.16.1 Prompt Injection dan Jailbreaking

Kerentanan fundamental dari LLM yang terintegrasi dalam aplikasi terletak pada kesulitan model untuk membedakan antara instruksi sistem yang terpercaya dengan data yang diberikan oleh pengguna yang tidak terpercaya (Ivry dan Nahum, 2025). Kerentanan ini dieksploitasi melalui dua kategori serangan utama, yaitu prompt injection dan jailbreaking.

Y. Liu dkk., 2025 mendefinisikan prompt injection sebagai manipulasi keluaran model bahasa melalui prompt jahat yang direkayasa secara khusus. Arsitektur aplikasi berbasis LLM umumnya terdiri dari penyedia layanan yang membuat serangkaian prompt yang telah ditentukan sebelumnya dan dikombinasikan dengan masukan pengguna sebelum dikirimkan ke LLM. Serangan prompt injection terjadi ketika seorang adversari menyisipkan instruksi berbahaya ke dalam masukannya sehingga dapat mempengaruhi atau menganulir prompt yang telah ditentukan sebelumnya dalam versi gabungannya. Y. Liu dkk., 2025 mengidentifikasi dua kategori utama serangan prompt injection yaitu kategori pertama menargetkan aplikasi dengan konteks atau prompt yang diketahui, di mana pengguna jahat menyuntikkan prompt berbahaya ke dalam masukannya untuk memanipulasi aplikasi agar merespon query yang berbeda dari tujuan aslinya dan kategori kedua merupakan serangan yang lebih canggih di mana adversari berupaya mencemari aplikasi berbasis LLM melalui sumber-sumber internet seperti situs web atau email yang mengandung payload berbahaya.

Sementara itu, jailbreaking merupakan jenis serangan yang berbeda namun berkaitan erat. Shen dkk., 2024 mendefinisikan jailbreak prompts sebagai prompt yang dirancang secara sengaja untuk melewati perlindungan bawaan LLM, sehingga memunculkan konten berbahaya yang melanggar kebijakan penggunaan yang ditetapkan oleh vendor LLM. Tidak seperti prompt injection yang memanipulasi konteks atau instruksi sistem, jailbreaking secara langsung

Page 54
<page_number>51</page_number>

menargetkan kemampuan keamanan yang ditanamkan selama proses pelatihan model.

Fomin, 2026 menekankan bahwa deteksi serangan prompt injection dan jailbreaking menjadi sangat kritis untuk deployment sistem Agentic AI yang aman, terutama karena agen-agen tersebut semakin banyak memproses data yang tidak terpercaya dari berbagai sumber seperti email, dokumen, keluaran tool, dan API eksternal. Fomin, 2026 juga mengidentifikasi bahwa tantangan utama dalam evaluasi model deteksi terletak pada distribution shift antara data pelatihan dan data dunia nyata, di mana banyak model menunjukkan penurunan performa yang signifikan ketika dihadapkan pada pola serangan baru yang belum pernah dijumpai sebelumnya.

Dalam penelitian ini, deteksi prompt injection dan jailbreaking diimplementasikan menggunakan model Llama Prompt Guard 2 yang dikembangkan oleh Meta AI (Meta, 2024). Model ini dirancang untuk mendeteksi dua kategori serangan utama yaitu prompt injections yang memanipulasi data pihak ketiga dan pengguna yang tidak tepercaya dalam context window untuk membuat model mengeksekusi instruksi yang tidak diinginkan, serta jailbreaks yang merupakan instruksi jahat yang dirancang untuk mengesampingkan fitur keamanan yang telah dibangun ke dalam model.

2.16.2 Blacklist Domain dengan LLM as Judge
Selain perlindungan terhadap serangan teknis berupa prompt injection dan jailbreaking, sistem Agentic AI yang berinteraksi dengan pengguna secara luas juga memerlukan mekanisme untuk membatasi topik-topik yang tidak relevan atau berpotensi merugikan. Dalam konteks penelitian ini, dua domain yang masuk dalam kategori blacklist adalah konten bermuatan SARA (Suku, Agama, Ras, dan Antargolongan) serta saran keuangan atau investasi yang bersifat personal. Pendekatan yang digunakan untuk deteksi blacklist domain adalah LLM as judge, di mana sebuah LLM dimanfaatkan sebagai evaluator untuk menilai apakah masukan pengguna termasuk dalam domain yang dilarang. Gu dkk., 2025 mendefinisikan LLM as judge sebagai pendekatan di mana LLM digunakan sebagai

Page 55
<page_number>52</page_number>

evaluator untuk tugas-tugas yang kompleks, memanfaatkan kemampuan LLM untuk meniru penalaran seperti manusia sambil menawarkan solusi yang efektif dari segi biaya dan dapat diskalakan dengan mudah. Secara formal, proses evaluasi LLM as judge dapat dinyatakan sebagai berikut:

$$\mathcal{E} \leftarrow \mathcal{P}{{LLM}}(\mathbf{x} \oplus C)$$ (2. 12)

dengan keterangan:

$\mathcal{E}$ adalah evaluasi akhir yang diperoleh dari seluruh proses LLM as judge dalam format yang diharapkan, yang dapat berupa skor, pilihan, label, atau kalimat.
$\mathcal{P}{{LLM}}$ adalah fungsi probabilitas yang didefinisikan oleh LLM yang bersangkutan, di mana pembangkitan dilakukan melalui proses autoregresif.
$\mathbf{x}$ adalah data masukan dalam bentuk yang tersedia, dalam hal ini berupa teks permintaan pengguna yang akan dievaluasi.
$C$ adalah konteks untuk masukan $\mathbf{x}$, yang umumnya berupa template prompt yang mendefinisikan aturan dan kriteria evaluasi.
$\oplus$ adalah operator kombinasi yang menggabungkan masukan $\mathbf{x}$ dengan konteks $C$
Pendekatan berbasis LLM as judge ini dipilih karena kemampuannya untuk memahami nuansa semantik dalam masukan yang tidak selalu dapat ditangkap oleh pendekatan berbasis aturan statis. Implementasi blacklist domain dalam penelitian ini difokuskan pada dua area kritis, yaitu konten bermuatan SARA dan saran keuangan atau investasi personal. Penyaringan konten SARA (suku, agama, ras, dan antargolongan) dilakukan untuk memitigasi risiko konflik sosial, polarisasi, dan penyebaran misinformasi yang dapat diperkuat secara sistemis oleh algoritma AI sehingga mengancam stabilitas nilai sosial (Ompusunggu dan Sinambela, 2025; Samson Olufemi Olanipekun, 2025; Santoso dkk., 2025). Di sisi lain, pembatasan terhadap saran keuangan personal diterapkan karena adanya risiko knowledge conflict antara data statis model dengan dinamika pasar real-time, potensi halusinasi pada konsep finansial yang kompleks, hingga adanya bias kognitif inheren yang dapat memicu kerugian finansial nyata bagi pengguna (Kang dan Liu, 2023; Lee dkk., 2025; Winder, Hildebrand dan Hartmann, 2025). Selain itu, proteksi ini

Page 56
<page_number>53</page_number>

berfungsi sebagai langkah preventif terhadap serangan prompt injection yang berpotensi mengeksploitasi workflow keuangan untuk melanggar regulasi kepatuhan (Ishrak Alim, 2025). Dengan memanfaatkan model Gemini 3 Flash sebagai evaluator, sistem mampu mendeteksi nuansa semantik dari permintaan pengguna secara lebih akurat dibandingkan metode pencocokan kata kunci konvensional, sebagai contoh pada Gambar 2.9 penerapan yang akan dilakukan LLM as judge pada penelitian ini.

<img>A diagram illustrating the "Overview sistem LLMs-as-judge" process. It shows three main sections: Input, System, and Output. The Input section includes Evaluation Type with options like Pointwise, Pairwise, Listwise, Evaluation Criteria with categories such as Fluency, Grammar, Relevance, Factuality, Informativeness, Completeness, and Evaluation References with Reference-Based and Reference-Free methods. The System section features a robot icon labeled "LLM-as-Judges" with Evaluation System options Single-LLM, Multiple-LLM, Human-AI, and a flowchart showing collaboration between robots and a human. The Output section displays Evaluation Results with icons for Score, Ranking, and Category, Explanation steps Reasoning Steps, Justifications, Decision-making leading to Results, and Feedback with Suggestions, Recommendations, and Improve arrows.</img>

Gambar 2.9 Overview sistem LLMs-as-judge (diadaptasi dari H. Li dkk., 2024)

2.17 Basis Data SQLite
SQLite merupakan sistem manajemen database relasional yang bersifat serverless, self-contained, dan dapat dijalankan tanpa proses server yang terpisah. Seluruh data database disimpan dalam satu file pada filesystem host, yang menjadikannya sangat sederhana dalam hal deployment dan tidak memerlukan konfigurasi server database yang kompleks. Sebagai mesin basis data yang paling banyak di-deploy di dunia, SQLite digunakan oleh berbagai peramban web terkemuka, sistem operasi, ponsel, dan sistem tertanam lainnya (SQLite, 2026).

Page 57
<page_number>54</page_number>

Dalam konteks sistem penelitian ini, SQLite berperan sebagai single source of truth yang menyimpan seluruh data persisten sistem, mencakup riwayat percakapan, serta hasil ekstraksi OCR dalam format JSON. Pilihan SQLite didasarkan pada beberapa pertimbangan teknis, yaitu kesederhanaan deployment dalam lingkungan pengembangan, performa baca-tulis yang memadai untuk skala penggunaan penelitian ini, dukungan native Python melalui modul sqlite3 standar, serta kompatibilitas dengan library aiosqlite untuk operasi database asinkron yang dibutuhkan dalam arsitektur FastAPI berbasis asyncio (FastAPI, 2026).

Erike dkk., 2025 melalui evaluasi performa komparatif antara SQLite, MySQL, dan Firebase menggunakan pendekatan parallel execution menemukan bahwa SQLite mencapai waktu rata-rata tercepat pada operasi baca sebesar 10,8 ms untuk data teks, mengungguli kedua kompetitornya. Keunggulan performa baca tersebut menjadi fondasi krusial bagi implementasi sistem memori yang dinamis pada LLM agent.

Penggunaan SQLite dalam penelitian ini selaras dengan konsep A-MEM (Agentic Memory) yang diusulkan oleh W. Xu dkk., 2025, di mana agen memerlukan sistem memori yang tidak hanya berfungsi sebagai penyimpanan statis, tetapi mampu mengorganisasikan pengalaman historis secara mandiri melalui pengindeksan dan keterhubungan antar data. Prinsip single writer diterapkan pada SQLite untuk menghindari race condition pada operasi tulis, di mana seluruh penulisan ke database dari sisi agent dilakukan secara eksklusif melalui MCP-SQLite sebagai satu-satunya titik akses yang dikontrol untuk operasi tulis dari layer agent.

2.18 Google Sheets
Google Sheets adalah platform spreadsheet berbasis cloud yang dikembangkan oleh Google dan dapat diakses melalui peramban web maupun aplikasi mobile tanpa memerlukan instalasi perangkat lunak tambahan. Platform ini menyediakan Google Sheets API sebagai antarmuka pemrograman yang memungkinkan aplikasi eksternal melakukan operasi baca (read) dan tulis (write)

Page 58
<page_number>55</page_number>

terhadap data spreadsheet secara programatik melalui protokol HTTP yang terstandarkan (De Matos dkk., 2025).

Dalam konteks sistem agentic yang membutuhkan output data yang dapat diakses dan dikelola oleh pengguna bisnis secara langsung, Google Sheets menjadi pilihan yang tepat sebagai repositori hasil data entry. Kemampuan kolaborasi real-time Google Sheets memungkinkan beberapa pengguna mengakses dan memantau data yang sama secara bersamaan, yang relevan dalam skenario di mana hasil ekstraksi struk perlu ditinjau atau diteruskan ke pihak lain dalam tim. Selain itu, antarmuka spreadsheet yang familiar bagi pengguna bisnis umum menjadikan Google Sheets sebagai format output yang tidak memerlukan kurva pembelajaran (learning curve) tambahan dari sisi pengguna akhir (end-user).

Integrasi Google Sheets dalam arsitektur sistem penelitian ini dilakukan melalui MCP-GSheets yang mengekspos Google Sheets API sebagai kumpulan tool yang dapat dipanggil oleh agent. Pendekatan ini memisahkan logika pengambilan keputusan agent dari implementasi teknis komunikasi dengan API Google, sehingga operasi seperti pembuatan sheet baru, pembaruan sel (cell), dan penambahan baris data dapat dilakukan oleh Data Entry Team Agent melalui tool yang terdefinisi dengan kontrak yang eksplisit. Pemilihan Google Sheets sebagai medium output data entry juga mempertimbangkan kemampuannya untuk berfungsi sebagai lapisan visualisasi data yang dapat langsung diolah lebih lanjut oleh pengguna, seperti pembuatan grafik, penerapan formula, atau ekspor ke format lain, tanpa ketergantungan pada sistem tambahan.

2.19 Evaluation Metrics
Evaluasi performa sistem Agentic AI untuk otomatisasi data entry memerlukan metrik yang mampu mengukur berbagai aspek kualitas secara komprehensif. Sistem yang dibangun dalam penelitian ini melibatkan dua tahapan utama yang masing-masing membutuhkan metrik evaluasi yang berbeda, yaitu tahapan ekstraksi informasi dari dokumen struk pembelian dan tahapan pemanggilan tool MCP oleh agent. Berdasarkan hal tersebut, penelitian ini menggunakan tiga kelompok metrik evaluasi yang saling melengkapi. Kelompok

Page 59
<page_number>56</page_number>

pertama adalah KIEval, yang mengukur kualitas ekstraksi informasi kunci dari dokumen dengan mempertimbangkan relasi struktural antar entitas. Kelompok kedua adalah ANLS*, yang mengevaluasi kemiripan antara output generatif model dengan ground truth menggunakan pendekatan berbasis jarak edit yang dinormalisasi dan mampu menangani struktur data yang kompleks. Kelompok ketiga adalah MCP tool accuracy, yang mengukur keakuratan pemanggilan tool oleh agent melalui dua sub-metrik, yaitu AST accuracy dan Pass@K accuracy.

2.19.1 Key Information Extraction Evaluation (KIEval)

Key Information Extraction Evaluation (KIEval) merupakan metrik evaluasi yang dirancang khusus untuk menilai performa model dokumen KIE dengan perspektif yang berorientasi pada kebutuhan aplikasi industri. Berbeda dari metrik konvensional seperti entity-level F1 score yang hanya menilai ekstraksi entitas secara individual tanpa mempertimbangkan relasi struktural antar entitas, KIEval diformulasikan untuk mengevaluasi model KIE pada dua tingkatan sekaligus, yaitu tingkat entitas (entity-level) dan tingkat grup (group-level). Motivasi pengembangan KIEval berakar pada dua permasalahan mendasar yang ditemukan pada metrik-metrik yang ada sebelumnya. Pertama, metrik yang ada mengabaikan sifat terstruktur dari informasi dalam dokumen, di mana pasangan kunci-nilai yang diekstraksi seringkali memiliki keterkaitan kontekstual satu sama lain, seperti pada data set CORD (Consolidated Receipt Dataset) relasi antara Menu.name, Menu.quantity, dan Menu.price pada dokumen struk pembelian. Kedua, formulasi metrik yang ada tidak selaras dengan kebutuhan aplikasi industri nyata, di mana kesalahan KIE lebih relevan diukur dalam satuan jumlah langkah koreksi yang diperlukan daripada pemisahan antara false positive (FP) dan false negative (FN) yang lazim digunakan pada metrik berbasis model (Khang dkk., 2025).

Inti dari KIEval adalah mekanisme group-matching yang dilakukan sebelum evaluasi pada tingkat entitas maupun grup. Misalkan PR = {pr₁, pr₂, ..., prₙ} adalah himpunan grup yang diprediksi dan GT = {gt₁, gt₂, ..., gtₘ} adalah himpunan grup ground truth, di mana setiap grup terdiri dari sekumpulan

Page 60
<page_number>57</page_number>

entitas yang direpresentasikan sebagai pasangan (entity-type, value). Skor pencocokan S(n, m) didefinisikan sebagai jumlah entitas identik antara prn dan gtm. Berdasarkan skor pencocokan tersebut, setiap grup prediksi dicocokkan dengan satu grup ground truth menggunakan Hungarian matching algorithm untuk menghasilkan himpunan grup yang telah dicocokkan:

G = Hungarian(PR, GT, S) (2. 13) di mana S menyatakan himpunan skor pencocokan S(n,m) antara seluruh pasangan prediksi dan ground truth. Untuk sebuah entitas e pada pasangan pencocokan (n, m), statistik TP, FN, dan FP kemudian dihitung sebagai berikut:

TPe(n,m) = Se(n,m), FN(e(n,m)) = Ne(gt(m)) - Se(n,m), FP(e(n,m)) = Ne(prn) - Se(n,m) (2. 14)

di mana Se(n,m) menyatakan jumlah pasangan entitas identik bertipe e antara grup prediksi ke-n dan grup ground truth ke-m, sedangkan Ne(·) menyatakan operasi penghitungan entitas bertipe e dalam suatu grup. Berdasarkan statistik tersebut, KIEval Entity F1 dihitung dengan mengakumulasi seluruh statistik TP, FN, dan FP dari seluruh pasangan dalam G sebagai berikut:

TPentity = ΣΣe TP(e(n,m)) (2. 15) (n,m)∈G M

FNentity = ΣΣe Ne(gt(m)) - TPentity (2. 16) m=1 N

FPentity = ΣΣe Ne(prn) - TPentity (2. 17)

Statistik-statistik tersebut kemudian digunakan untuk menghitung KIEval Entity F1 menggunakan formulasi presisi dan recall standar. Untuk evaluasi tingkat grup, KIEval Group F1 dievaluasi pada himpunan G', yaitu himpunan G tanpa elemen pertamanya yang merepresentasikan entitas non-grup seperti company.name dan company.number:

G' = G \ (n₁, m₁) (2. 18)

TPgroup = Σ 1! [Se(n,m) = Ne(gt(m)) = Ne(prn) ∀e] (2. 19) (n,m)∈G'

di mana 1[·] adalah operator biner yang bernilai 1 apabila grup prediksi dan ground truth identik secara keseluruhan pada seluruh tipe entitas e. FN dan FP pada tingkat

Page 61
<page_number>58</page_number>

grup dihitung sebagai jumlah grup ground truth dan prediksi yang tidak memiliki pasangan dalam $G'$.

Selain evaluasi berbasis F1, KIEval juga memperkenalkan KIEval$_{\text{Aligned}}$ yang memformulasikan kesalahan KIE dalam satuan biaya koreksi yang lebih selaras dengan setting aplikasi industri. Untuk setiap entitas e pada pasangan pencocokan $(n,m) \in G$, tiga jenis koreksi didefinisikan sebagai berikut:

Subs${(n,m)}^{e} = \min !\left(FP{(n,m)}^{e}, FN_{(n,m)}^{e}\right)$ (2. 20) Add${(n,m)}^{e} = FN{(n,m)}^{e} - Subs_{(n,m)}^{e}$ (2. 21) Del${(n,m)}^{e} = FP{(n,m)}^{e} - Subs_{(n,m)}^{e}$ (2. 22)

di mana substitusi didefinisikan sebagai jumlah minimum dari FP dan FN, yang menyatakan banyaknya prediksi yang memerlukan modifikasi agar sesuai dengan nilai ground truth yang bersesuaian. Penambahan (addition) dan penghapusan (deletion) masing-masing merupakan sisa FN dan FP setelah dikurangi substitusi.

Total jumlah kesalahan kemudian dihitung sebagai:

Error = $\sum_{(n,m) \in G} \sum_{e} Error_{(n,m)}^{e} + \sum_{(,m) \notin G} \sum_{e} N_{e}(gt_{m}) + \sum_{(n,) \notin G} \sum_{e} N_{e}(pr_{n})$ (2. 23)

di mana suku pertama menyatakan jumlah koreksi pada pasangan grup yang cocok, suku kedua menyatakan penambahan untuk grup ground truth yang tidak memiliki pasangan prediksi, dan suku ketiga menyatakan penghapusan untuk grup prediksi yang tidak memiliki pasangan ground truth. Akhirnya, KIEval$_{\text{Aligned}}$ dihitung sebagai:

KIEval$_{\text{Aligned}} = \frac{TP^{\text{entity}}}{TP^{\text{entity}} + \text{Error}}$ (2. 24)

Formulasi KIEval$_{\text{Aligned}}$ tidak hanya lebih selaras dengan setting aplikasi industri, tetapi juga memiliki interpretabilitas tinggi karena dinyatakan sepenuhnya dalam komponen yang sudah dikenal, yaitu TP, FP, dan FN.

Dalam konteks penelitian ini, KIEval diterapkan untuk mengukur kualitas ekstraksi informasi kunci dari struk pembelian yang dihasilkan oleh extraction agent berbasis GLM-OCR. Metrik KIEval Entity F1 mengukur sejauh mana entitas-entitas individual seperti nama toko, tanggal transaksi, nama item, dan harga diekstraksi dengan benar, sedangkan KIEval Group F1 mengukur apakah item-item

Page 62
<page_number>59</page_number>

beserta atributnya, yaitu nama item, kuantitas, harga satuan, dan total harga, dikelompokkan secara tepat sebagaimana yang tercantum pada struk asli.

2.19.2 Average Normalized Levenshtein Similarity Star (ANLS*)

Average Normalized Levenshtein Similarity star (ANLS*) merupakan metrik evaluasi universal yang dirancang untuk menilai performa model generatif pada berbagai tugas pemrosesan dokumen, termasuk ekstraksi informasi dan klasifikasi. Metrik ini diperkenalkan oleh Peer dkk., 2025 sebagai pengembangan dan pengganti langsung dari metrik ANLS yang telah ada sebelumnya, dengan kemampuan yang diperluas untuk menangani tipe data yang lebih beragam, meliputi string, None, Tuple, List, Dictionary, serta berbagai kombinasi rekursifnya. Motivasi pengembangan ANLS* berasal dari keterbatasan yang ditemukan pada metrik-metrik sebelumnya ketika diterapkan pada model bahasa generatif berskala besar. Metrik berbasis exact match seperti F1 score tidak sesuai untuk model generatif karena output yang dihasilkan berupa teks bebas yang mungkin mengandung variasi kecil namun secara semantik masih benar. Di sisi lain, metrik ANLS yang ada hanya mendukung perbandingan string dan daftar sederhana, sehingga tidak dapat digunakan untuk mengevaluasi output berbentuk kamus bersarang yang umum dijumpai pada tugas ekstraksi informasi terstruktur dari dokumen.

Ide utama dari ANLS* adalah merepresentasikan ground truth dan prediksi sebagai struktur pohon, kemudian menghitung pencocokan antara kedua pohon tersebut secara dinormalisasi. Dengan pendekatan ini, ANLS* mampu mengevaluasi kesamaan antara struktur prediksi dan ground truth secara lebih komprehensif dibandingkan metrik berbasis pencocokan sederhana. Perhitungan skor tidak hanya mempertimbangkan kesamaan teks pada tingkat karakter melalui jarak Levenshtein, tetapi juga mempertimbangkan kesesuaian struktur data yang dihasilkan oleh model generatif. Hal ini menjadikan ANLS* sangat relevan untuk tugas pemrosesan dokumen modern yang sering menghasilkan keluaran dalam bentuk struktur data kompleks seperti dictionary bersarang atau daftar objek. Metrik ini memberikan evaluasi yang lebih representatif terhadap performa model

Page 63
<page_number>60</page_number>

generatif dalam mengekstraksi dan merepresentasikan informasi terstruktur dari dokumen. Secara formal, ANLS* didefinisikan sebagai rasio antara skor s dan ukuran l dari representasi pohon ground truth dan prediksi:

$$\text{ANLS}^*(g,p) = \frac{s(g,p)}{l(g,p)} \quad (2.25)$$

di mana g adalah ground truth, p adalah prediksi, sehingga $\text{ANLS}^*(g,p) \in [0,1]$.

Setiap prediksi dalam pohon tersebut diberikan bobot yang setara, sehingga simpul daun (leaf nodes) pada sub-pohon besar memiliki bobot yang sama dengan simpul daun yang muncul di tingkat atas.

Fungsi skor s didefinisikan secara rekursif untuk mengukur kemiripan antara ground truth dan prediksi, disesuaikan dengan tipe data masing-masing:

$$s(g,p) = \begin{cases} 1.0 & \ 1.0 - \frac{\text{LD}(g,p)}{\max(|g|,|p|)} & \ s(g_i,p) \text{ with } i = \argmax_i \left( \text{ANLS}^*(g_i,p) \right) & \ \sum_{(g_i,p_i) \in \psi(g,p)} s(g_i,p_i) & \ \sum_{k \in \text{keys}(p)} s(g_k,p_k) & \ 0.0 & \end{cases} \quad (2.26)$$

if type(g) = type(p) = None if type(g) = type(p) = String and s(g,p) ≥ τ if type(g) = Tuple if type(g) = type(p) = List if type(g) = type(p) = Dict and k ∈ keys(p) otherwise

di mana LD adalah jarak Levenshtein, τ = 0,5 adalah ambang batas normalized Levenshtein distance yang apabila dilampaui maka skor dianggap 0, dan ψ adalah algoritma Hungarian matching yang dieksekusi berdasarkan skor ANLS* berpasangan antara setiap elemen ground truth dan prediksi. Ketidakcocokan tipe (type mismatch) menghasilkan skor 0.0.

Untuk menormalisasi skor s, fungsi panjang l didefinisikan secara rekursif pada rumus 2.27 sebagai berikut:

Page 64
<page_number>61</page_number>

graph LR
    A[l(g,p)] --> B[l(g,p) with i = arg max 2i(ANLS*(g,p))]
    B --> C[1]
    B --> D[1]
    B --> E[∑l(gi,pi) for (gi,pi) ∈ ψ(g,p)]
    B --> F[∑lt(gu) for gu ∈ ψ(g,p)]
    B --> G[∑lt(pu) for pu ∈ ψ(g,p)]
    B --> H[∑l(gk,pk) for k ∈ keys(p) ∩ keys(g)]
    B --> I[∑lt(gk) for k ∈ keys(g) - keys(p)]
    B --> J[∑lt(pk) for k ∈ keys(p) - keys(g)]
    B --> K[max(lt(g), lt(p))]
(2. 27)

graph LR
    A[l_t(x)] -->|if type(x) = None| B[1]
    A -->|if type(x) = String| C[1]
    A -->|if type(x) = Tuple| D[∑_{x_i ∈ x} l_t(x_i)]
    A -->|if type(x) = List| E[∑_{x_i ∈ x} l_t(x_i)]
    A -->|if type(x) = Dict| F[∑_{k ∈ keys(x)} l_t(x_k)]
(2. 28)

Ketidakcocokan tipe pada sub-pohon ditangani melalui fungsi panjang l_t yang didefinisikan sebagai berikut:

graph LR
    A[l_t(x)] -->|if type(x) = None| B[1]
    A -->|if type(x) = String| C[1]
    A -->|if type(x) = Tuple| D[∑_{x_i ∈ x} l_t(x_i)]
    A -->|if type(x) = List| E[∑_{x_i ∈ x} l_t(x_i)]
    A -->|if type(x) = Dict| F[∑_{k ∈ keys(x)} l_t(x_k)]
di mana x adalah sub-pohon dari prediksi p maupun sub-pohon dari ground truth g.

Penggunaan max(l_t(g), l_t(p)) pada kasus ketidakcocokan tipe memastikan bahwa baik sub-pohon yang hilang maupun sub-pohon yang dihalusinasi mendapatkan penalti yang setara.

Page 65
<page_number>62</page_number>

Keunggulan ANLS* dibandingkan metrik-metrik sebelumnya terletak pada kemampuannya menangani berbagai tipe data secara rekursif dalam satu kerangka yang terpadu. Pada tipe String, digunakan normalized levenshtein similarity dengan ambang batas τ = 0,5, sehingga prediksi dengan jarak edit melebihi setengah panjang string dianggap salah total. Pada tipe List, algoritma Hungarian matching digunakan untuk menemukan pasangan optimal antara elemen-elemen prediksi dan ground truth tanpa memperhatikan urutan, sehingga elemen yang hilang maupun yang dihalusinasi mendapat penalti. Pada tipe Dict, pencocokan dilakukan berdasarkan kunci, sehingga kunci yang hilang maupun yang dihalusinasi mendapat penalti secara simetris.

Dalam konteks penelitian ini, ANLS* digunakan sebagai metrik komplementer untuk mengevaluasi kualitas keluaran JSON yang dihasilkan oleh extraction agent. Kemampuan ANLS* dalam menangani output berbentuk kamus bersarang menjadikannya sangat relevan untuk mengevaluasi skema JSON ekstraksi struk pembelian yang memiliki struktur hierarkis dengan field info, items, dan payment. Penggunaan normalized levenshtein distance juga memungkinkan toleransi terhadap variasi kecil dalam format string yang umum terjadi pada dokumen struk pembelian, seperti perbedaan penulisan tanggal, nama produk yang disingkat, atau format harga yang berbeda-beda antar toko.

2.19.3 MCP Tool Accuracy
Evaluasi akurasi penggunaan tool MCP oleh agent memerlukan metrik yang mampu mengukur dua aspek yang berbeda namun saling melengkapi. Aspek pertama adalah kebenaran setiap pemanggilan tool secara individual, yang diukur menggunakan metrik AST accuracy. Aspek kedua adalah kebenaran output akhir dari keseluruhan workflow, yang diukur menggunakan metrik Pass@K. Kombinasi kedua metrik ini memberikan gambaran komprehensif tentang kemampuan agent dalam memilih tool yang tepat, mengisi parameter dengan benar, dan menghasilkan output yang sesuai dengan ekspektasi. Fan dkk., 2025 dalam benchmark MCPToolBench++ menunjukkan bahwa peringkat AST accuracy dan Pass@K tidak selalu berkorelasi positif, sehingga kedua metrik tersebut diperlukan secara bersamaan untuk diagnosis performa yang lebih lengkap.

Page 66
<page_number>63</page_number>

Abstract Syntax Tree (AST)
Abstract Syntax Tree (AST) merupakan metrik yang mengukur kebenaran setiap pemanggilan tool oleh agent dengan cara membandingkan output yang dihasilkan terhadap label ground truth menggunakan pendekatan pohon sintaksis abstrak. Pendekatan ini pertama kali diperkenalkan secara sistematis oleh Patil dkk., 2025 pada Berkeley Function Calling Leaderboard (BFCL) dan kemudian diadopsi secara luas untuk evaluasi MCP tool use. Evaluasi AST bersifat all-or-nothing atau exact match, di mana sebuah pemanggilan tool hanya dianggap benar jika seluruh komponennya tepat secara bersamaan tanpa toleransi terhadap kesalahan parsial.

Tiga komponen yang dievaluasi dalam AST Accuracy adalah sebagai berikut. Pertama, kecocokan nama fungsi (function match), yang memverifikasi bahwa nama tool yang dipanggil oleh agent sesuai dengan ground truth. Kedua, kecocokan parameter wajib (required parameter match), yang memastikan seluruh parameter yang diwajibkan oleh skema tool tersedia dalam panggilan dan tidak ada parameter yang tidak dikenal dari skema yang digunakan. Ketiga, kecocokan tipe dan nilai parameter (parameter type and value match), yang memverifikasi bahwa tipe data dan nilai dari setiap parameter sesuai dengan ekspektasi ground truth secara tepat. Skor AST untuk satu pemanggilan tool ke-i didefinisikan menggunakan logika konjungsi (AND), di mana pemanggilan tool hanya dianggap benar jika seluruh komponen tersebut terpenuhi:

$$\text{AST}_i = 1 \left[ (\widehat{f_i} = f_i) \land \left( p_i^{\overline{\text{req}}} = p_i^{\text{req}} \right) \land \left( p_i^{\overline{\text{val}}} = p_i^{\text{val}} \right) \right] \quad (2. 29)$$

di mana $f_i$ adalah nama fungsi ground truth, $\widehat{f_i}$ adalah nama fungsi yang diprediksi oleh agent, $p_i^{\text{req}}$ adalah himpunan parameter wajib ground truth, $p_i^{\overline{\text{req}}}$ adalah himpunan parameter wajib yang diprediksi, $p_i^{\text{val}}$ adalah himpunan tipe dan nilai parameter ground truth, $\overline{p_i^{\text{val}}}$ adalah himpunan tipe dan nilai parameter yang diprediksi, dan $1[\cdot]$ adalah fungsi indikator yang bernilai 1 jika seluruh kondisi terpenuhi dan bernilai 0 jika terdapat satu kondisi saja yang tidak sesuai.

AST accuracy untuk satu test case yang melibatkan $M$ pemanggilan tool adalah rata-rata skor seluruh pemanggilan tool dalam test case tersebut:

Page 67
<page_number>64</page_number>

AST_Accuracy_j = 1/M ∑_{i=1}^{M} AST_i (2.30)

Untuk keseluruhan dataset yang terdiri dari N test case, AST accuracy dihitung sebagai rata-rata dari seluruh test case:

1/AST_Accuracy = 1/N ∑_{j=1}^{N} AST_Accuracy_j (2.31)

Pass@K
Pass@K merupakan metrik yang mengukur peluang agent menghasilkan output akhir yang benar setidaknya dalam satu dari K percobaan independen. Metrik ini pertama kali diperkenalkan oleh Chen dkk., 2021 dalam konteks evaluasi model code generation pada benchmark HumanEval untuk mengatasi keterbatasan metrik exact match sederhana dalam mengakomodasi variabilitas stokastik output model generatif. Kemampuan pass@k untuk mengukur fungsional kebenaran, yaitu apakah output memenuhi kriteria kebenaran yang ditetapkan daripada hanya mencocokkan string secara harfiah, menjadikannya metrik yang lebih representatif untuk mengevaluasi sistem agentic yang menghasilkan output berupa tindakan nyata seperti penulisan data ke spreadsheet.

Secara formal, untuk mengevaluasi Pass@K, sebanyak n ≥ k sampel dihasilkan per test case, kemudian dihitung jumlah sampel yang benar c ≤ n yang memenuhi kriteria kebenaran yang ditetapkan. Estimator unbiased dari Pass@K yang menghindari varians tinggi dari estimasi naif didefinisikan sebagai berikut:

pass@k = 1 - (n-c choose k) / (n choose k) (2.32)

di mana n adalah total sampel yang dihasilkan per test case, c adalah jumlah sampel yang benar, dan k adalah jumlah sampel yang dipilih untuk evaluasi.

Untuk sistem data entry pada penelitian ini, Pass@K digunakan dalam konfigurasi K = 1 (Pass@1) dengan n = 1 sampel per test case, karena sistem produksi mensyaratkan kebenaran pada percobaan pertama tanpa mekanisme retry. Dalam kondisi khusus ini, estimator menyederhanakan menjadi ekspektasi keberhasilan empiris, dan indikator keberhasilan untuk satu test case j didefinisikan sebagai:

Page 68
<page_number>65</page_number>

Pass@1j = cj,1 = { 1 Jika output akhir agent ≡ ground truth 0 Jika sebaliknya (2.33)

di mana cj,1 ∈ {0,1} adalah indikator keberhasilan percobaan ke-1 pada test case j, yang bernilai 1 jika output akhir agent sesuai dengan ground truth dan bernilai 0 jika tidak. Pass@1 keseluruhan untuk dataset dengan N test case kemudian dihitung sebagai:

$\overline{\text{Pass@1}} = \frac{1}{N} \sum_{j=1}^{N} \text{Pass@1}_j$ (2.34)

Dalam konteks penelitian ini, Pass@1 mengukur apakah keseluruhan workflow agent, mulai dari pembacaan dokumen oleh extraction agent, pengambilan keputusan oleh supervisor agent, hingga penulisan data ke Google Sheets oleh Data Entry Team melalui MCP, menghasilkan output akhir yang benar pada percobaan pertama. Sebuah test case dianggap berhasil (Pass@1 = 1) apabila seluruh data yang tertulis ke dalam spreadsheet sesuai dengan ground truth yang telah dianotasi secara manual, mencakup kebenaran nilai entitas, kelengkapan struktur, dan keakuratan penempatan data pada baris dan kolom yang tepat.

Kombinasi antara AST dan Pass@1 saling melengkapi dalam mengevaluasi performa sistem secara menyeluruh. AST mengukur process quality agent dalam mengeksekusi MCP tools, mencakup kebenaran nama fungsi, parameter wajib, serta nilai parameter yang dipanggil pada setiap langkah eksekusi. Sementara itu, Pass@1 mengukur outcome quality yang dihasilkan sistem, yaitu apakah data struk yang diekstraksi berhasil ditulis secara benar ke Google Sheets dalam satu kali percobaan tanpa retry.

2.20 React Native dan Expo
React Native adalah framework pengembangan aplikasi mobile lintas platform (cross-platform) yang dikembangkan oleh Meta dan pertama kali dirilis secara publik pada tahun 2015 (Hutri, 2023). Framework ini memungkinkan pengembang membangun aplikasi native untuk Android dan iOS menggunakan satu basis kode tunggal (single codebase) yang ditulis dalam JavaScript dengan

Page 69
<page_number>66</page_number>

komponen React, sehingga secara signifikan mengurangi effort pengembangan dibandingkan dengan pendekatan native yang memerlukan basis kode terpisah untuk setiap platform (Ali dan Shubham, 2020). React Native mengompilasi komponen JavaScript ke komponen UI native platform yang sesungguhnya, bukan ke dalam WebView, sehingga menghasilkan performa dan tampilan yang tidak berbeda dari aplikasi yang dibangun menggunakan bahasa native platform secara langsung.

Expo adalah toolchain dan managed runtime yang dibangun di atas React Native, menyediakan lapisan abstraksi yang menyederhanakan proses pengembangan, build, dan distribusi aplikasi. Expo menawarkan platform-neutral API yang mengizinkan pengembang mengakses fitur perangkat native seperti kamera dan notifikasi tanpa perlu menulis kode yang berspesifik pada platform tertentu. Keunggulan Expo dibandingkan penggunaan React Native secara langsung meliputi kemudahan konfigurasi proyek, lingkungan build yang terkelola (managed), serta dukungan bawaan untuk deployment ke Android, iOS, dan web dari satu proyek yang sama.

Dalam penelitian ini, React Native dengan Expo digunakan sebagai framework pengembangan antarmuka pengguna (user interface) sistem dengan fokus implementasi pada platform mobile iOS. Meskipun implementasi difokuskan pada iOS, arsitektur cross-platform React Native dan Expo tetap memungkinkan perluasan ke platform Android dan web browser di masa mendatang tanpa memerlukan penulisan ulang basis kode secara substansial. Expo Router digunakan sebagai solusi navigasi berbasis file system yang konsisten dengan pendekatan routing pada aplikasi web modern, memfasilitasi pengembangan tiga halaman utama sistem, yaitu antarmuka percakapan dengan AI agent, tampilan WebView Google Sheets secara real-time, serta halaman profil pengguna.

2.21 Agile Scrum
Secara umum, metode pengembangan perangkat lunak dapat diklasifikasikan menjadi dua paradigma utama. Paradigma pertama adalah pendekatan plan-driven yang mencakup metode sekuensial

Page 70
<page_number>67</page_number>

seperti Waterfall serta metode iteratif formal seperti Rational Unified Process (RUP). Pendekatan ini sangat mengandalkan perencanaan matang dan dokumentasi lengkap di awal. Paradigma kedua adalah pendekatan agile, seperti Scrum, yang bersifat empiris dan adaptif. Berdasarkan penelitian Shafiee dkk., 2020, transisi dari RUP ke Scrum terbukti memberikan dampak positif dalam menghadapi fleksibilitas pengembangan sistem yang kompleks, yang mana sangat relevan dengan karakteristik pengembangan Agentic AI berbasis model generatif dengan komponen fine-tuning, integrasi MCP, dan evaluasi model yang memerlukan penyesuaian berkelanjutan berdasarkan hasil eksperimen, sehingga pendekatan Agile Scrum lebih sesuai untuk konteks ini.

Agile merupakan metodologi pengembangan perangkat lunak yang menekankan nilai-nilai adaptabilitas, kolaborasi, dan pengiriman perangkat lunak yang berfungsi secara inkremental (Abrahamsson dkk., 2017). Manifesto Agile yang dipublikasikan pada tahun 2001 menetapkan empat nilai utama yaitu individu dan interaksi lebih diutamakan daripada proses dan alat, perangkat lunak yang berfungsi lebih diutamakan daripada dokumentasi yang komprehensif, kolaborasi dengan pelanggan lebih diutamakan daripada negosiasi kontrak, dan respons terhadap perubahan lebih diutamakan daripada mengikuti rencana yang telah ditetapkan. Prinsip-prinsip ini relevan dalam pengembangan sistem AI modern, di mana integrasi AI ke dalam metodologi Agile terbukti meningkatkan efisiensi pengembangan, akurasi, dan keamanan sistem sekaligus mengurangi waktu pengembangan (Cabrero-Daniel, 2023).

Scrum adalah salah satu implementasi Agile yang paling banyak digunakan, mengadopsi pendekatan empiris yang menerapkan konsep kontrol proses industri ke dalam pengembangan sistem. Scrum membagi proses pengembangan ke dalam tiga fase utama.

Fase Pre-Game mencakup perencanaan keseluruhan proyek dan penyusunan Product Backlog, yaitu daftar kebutuhan sistem yang diprioritaskan dan diperbarui secara berkelanjutan selama proses pengembangan.
Page 71
<page_number>68</page_number>

Fase Development (Game) merupakan inti dari Scrum yang terdiri dari serangkaian Sprint, yaitu siklus iteratif berdurasi satu hingga empat minggu di mana tim mengembangkan increment sistem yang dapat berfungsi.
Fase Post-Game mencakup integrasi akhir, pengujian sistem secara menyeluruh, dan persiapan rilis.
Penerapan Agile Scrum dalam penelitian ini relevan mengingat temuan Cabrero-Daniel, 2023 yang menunjukkan bahwa integrasi AI dalam proses Agile dapat membantu mengidentifikasi dependensi dan konflik kebutuhan, memprioritaskan backlog, serta mengotomatisasi tugas-tugas pengembangan yang berulang.

2.22 Flowchart
Flowchart didefinisikan sebagai suatu diagram yang merepresentasikan secara visual urutan langkah-langkah yang terlibat dalam suatu proses atau sistem. Setiap langkah digambarkan menggunakan simbol tertentu, sedangkan panah digunakan untuk menunjukkan alur kendali atau aliran data antar langkah tersebut. Flowchart dimanfaatkan untuk memodelkan sistem atau proses sehingga memudahkan pengguna dalam memahami struktur serta urutan kejadian yang terjadi di dalamnya (Ghritlahare, 2025).

Tabel 2. 5 Simbol - simbol flowchart diagram

Simbol	Nama	Keterangan
<img>Rectangle</img>	Proses	Sebuah proses yang dilakukan oleh komputer umumnya menghasilkan perubahan pada data atau informasi yang diproses.
<img>Parallelogram</img>	Input atau Output	Untuk menunjukkan proses masukan atau keluaran data dalam alur sistem.
<img>Diamond</img>	Decision (Logika)	Untuk menyatakan suatu kondisi dengan dua kemungkinan hasil, yaitu YA atau TIDAK.
Page 72
<page_number>69</page_number>

<img>Predefined Process icon</img>	Predefined Process	Untuk menunjukkan penyediaan ruang penyimpanan dalam pemrosesan data agar menetapkan nilai awal.
<img>Terminal icon</img>	Terminal	Untuk menunjukkan titik awal atau akhir dari suatu program.
2.23 Unified Modeling Language (UML)
Unified Modeling Language atau UML digunakan dalam pengembangan sistem pada bidang rekayasa perangkat lunak sebagai bahasa visual untuk mendefinisikan dan mendokumentasikan suatu sistem. Melalui UML, kebutuhan sistem yang digambarkan dalam bentuk skenario penggunaan oleh pengguna dapat direpresentasikan secara jelas. Selain itu, berbagai batasan yang terdapat dalam sistem juga dapat dimodelkan menggunakan UML. Oleh karena itu, banyak peneliti yang bergerak di bidang rekayasa perangkat lunak mempublikasikan kajian mengenai pemanfaatan diagram UML dalam pengembangan sistem serta kontribusinya terhadap praktik rekayasa perangkat lunak guna mendukung perkembangan disiplin ilmu tersebut (Koç dkk., 2021).

Use Case Diagram

Use case diagram merupakan diagram dalam UML yang digunakan untuk menggambarkan hubungan antara aktor dan fungsi-fungsi yang disediakan oleh sistem secara visual. Diagram ini menampilkan aktor sebagai pihak yang berinteraksi dengan sistem serta use case sebagai representasi layanan atau proses yang dapat dijalankan untuk mencapai tujuan tertentu. Use case diagram berfungsi memberikan gambaran umum mengenai ruang lingkup sistem, batasan sistem, serta interaksi yang terjadi antara pengguna dan sistem tanpa menjelaskan detail alur langkah di dalamnya. Dengan penyajian yang sederhana dan mudah dipahami, use case diagram membantu pemangku kepentingan dalam memahami kebutuhan fungsional sistem serta menjadi dasar dalam proses analisis dan perancangan sistem perangkat lunak (Vranić dkk., 2024).

Page 73
<page_number>70</page_number>

Tabel 2. 6 Simbol – simbol use case diagram

Gambar	Nama	Keterangan
<img>A stick figure with a head and body.</img>	Aktor	Ketika aktor berkomunikasi dengan use case, mereka dapat berupa individu, sistem lain, atau alat.
<img>A dashed arrow pointing to the right.</img>	Ketergantungan (dependency)	Hubungan di mana elemen yang tidak bersifat mandiri bergantung pada elemen yang berdiri sendiri jika diubah.
<img>An arrow pointing left.</img>	Generalisasi	Menunjukkan bahwa seorang aktor memiliki kemampuan khusus yang memungkinkannya berpartisipasi dalam suatu kasus.
<img>A dashed arrow pointing right.</img>	*Include*	Ini menunjukkan bahwa suatu kebutuhan sepenuhnya terintegrasi dalam fungsionalitas kebutuhan lain yang terkait.
<img>An arrow pointing left.</img>	*Extend*	Menunjukkan bahwa sebuah use case menjadi perluasan fungsional dari use case lain ketika sebuah kondisi tertentu terpenuhi.
<img>A straight line.</img>	Asosiasi	Pemetaan umum hubungan antara aktor dan kasus.
<img>A rectangle.</img>	Sistem	Menspesifikasikan paket yang menunjukkan sistem yang memiliki batasan tertentu.
<img>An oval shape.</img>	Kasus (*use case*)	Fungsionalitas yang ditawarkan oleh sistem dalam bentuk unit-unit yang dapat berinteraksi satu sama lain dengan bertukar pesan antar aktor atau unit.
Activity Diagram
Activity diagram merupakan salah satu diagram dalam UML yang digunakan untuk menggambarkan perilaku sistem dalam bentuk alur kendali dari satu aktivitas ke aktivitas lainnya. Diagram ini merepresentasikan rangkaian tindakan yang dilakukan secara terkoordinasi oleh sistem untuk mencapai suatu

Page 74
<page_number>71</page_number>

tujuan tertentu. Alur aktivitas dimulai dari titik awal dan berakhir pada titik akhir, dengan setiap aktivitas digambarkan sebagai langkah kerja yang saling terhubung melalui panah sebagai penunjuk aliran proses. Activity diagram juga mendukung percabangan, penggabungan, serta proses paralel untuk memodelkan berbagai kemungkinan alur yang dapat terjadi dalam sistem. Selain itu, diagram ini dapat dibagi ke dalam swimlane untuk menunjukkan pihak atau aktor yang bertanggung jawab terhadap setiap aktivitas. Dengan demikian, activity diagram membantu dalam memahami proses bisnis atau logika sistem secara terstruktur dan sistematis (Siewe dan Ngounou, 2025).

Tabel 2. 7 Simbol – simbol activity diagram

Gambar	Nama	Keterangan
<img>A rectangle with rounded corners.</img>	Aktivitas	Menunjukkan interaksi antarmuka kelas.
<img>An oval shape.</img>	Action	Keadaan sistem yang menunjukkan pelaksanaan tindakan tertentu.
<img>A solid circle.</img>	Node Permulaan	Kondisi awal yang dicapai sistem ditunjukkan dalam diagram aktivitas sebagai kondisi awal.
<img>A hollow circle with a black dot inside.</img>	Aktivitas Node Akhir	Kondisi akhir yang dicapai sistem juga ditunjukkan dalam diagram aktivitas sebagai kondisi akhir.
<img>A horizontal line with a black bar.</img>	Node Cabang	Sebuah aliran yang akhirnya bercabang menjadi banyak aliran.
<img>A diamond shape.</img>	Keputusan	Ketika ada lebih dari satu pilihan atau aktivitas, itu disebut asosiasi percabangan.
Class Diagram
UML class diagram merupakan diagram yang digunakan untuk memodelkan struktur statis suatu sistem dengan menampilkan kelas, atribut, operasi, serta hubungan antar kelas. Dalam rekayasa perangkat lunak berbasis

Page 75
<page_number>72</page_number>

model, diagram kelas banyak dimanfaatkan dalam berbagai proses seperti refactoring dan transformasi, termasuk untuk perbaikan desain, peningkatan keterpeliharaan, penerapan pola desain, hingga pembangkitan kode dan skema basis data. Untuk mengevaluasi sistem atau perangkat lunak yang memproses diagram kelas secara efektif, diperlukan cakupan berbagai variasi struktur diagram yang representatif. Salah satu pendekatan yang dapat digunakan adalah dengan mengelompokkan diagram ke dalam kelas-kelas kesetaraan struktural, sehingga pengujian dapat dilakukan secara efisien dengan memilih diagram perwakilan dari setiap kelompok. Pendekatan ini memungkinkan evaluasi yang lebih sistematis dan komprehensif terhadap kinerja serta ketahanan alat bantu rekayasa perangkat lunak yang berbasis UML (Tazin dan Kokar, 2025).

Tabel 2. 8 Simbol – simbol class diagram

Gambar	Nama	Keterangan
<img>Package icon</img>	Package	Paket adalah kumpulan satu atau lebih kelas yang dikemas dalam satu paket.
<img>Class diagram with attributes and operations</img>	Kelas	Dalam struktur sistem, setiap kelas memiliki nama, set properti, dan set operasi atau metode.
<img>Interface icon</img>	Antarmuka	Sama dengan prinsip pemrograman berorientasi objek.
<img>Unidirectional association line</img>	Hubungan	Koneksi antara kelas-kelas yang tidak didefinisikan secara khusus..
<img>Directed association line</img>	Hubungan berarah	Hubungan antara kelas yang mengindikasikan bahwa satu kelas digunakan oleh kelas lainnya.
<img>Generalization line</img>	Generalisasi	Hubungan antar kelas yang mencerminkan hierarki umum–khusus, di mana suatu kelas umum
Page 76
<page_number>73</page_number>

memiliki kelas-kelas spesifik yang mewarisi karakteristiknya.
<img>Arrow pointing right</img>	Kebergantungan	Hubungan kelas menunjukkan bahwa dalam situasi tertentu, satu kelas membutuhkan kelas lainnya, menunjukkan ketergantungan antara kelas.
Agregasi	Keterkaitan antar kelas yang menggambarkan konsep keseluruhan-bagian, di mana satu kelas merupakan bagian dari atau terkait dengan keseluruhan yang lebih besar.
Sequence Diagram
Sequence diagram merupakan salah satu diagram perilaku dalam UML yang digunakan untuk menggambarkan interaksi antar objek serta pertukaran pesan yang terjadi seiring waktu. Diagram ini menunjukkan bagaimana peristiwa atau aktivitas dalam suatu use case dipetakan ke dalam operasi pada kelas-kelas yang terdapat pada class diagram. Sequence diagram banyak digunakan pada tahap perancangan rinci untuk memodelkan komunikasi antar objek secara terstruktur sesuai dengan kebutuhan sistem. Sifatnya yang intuitif dan mudah dipahami menjadikan diagram ini populer dalam membantu pengguna maupun pengembang memahami alur kerja sistem dan hubungan antar objek. Selain itu, sequence diagram juga dapat dimanfaatkan untuk menggambarkan alur pemanggilan metode, spesifikasi interaksi pada sistem terdistribusi, serta sebagai dasar dalam proses pengujian sistem (Al-Fedaghi, 2021).

Tabel 2. 9 Simbol – simbol sequence diagram

Gambar	Nama	Keterangan
<img>Actor symbol</img>	Aktor	Actor memiliki peran orang ketika berkomunikasi dengan sistem yang
Page 77
<page_number>74</page_number>

dibuat, bisa berupa individu, sistem lain, atau alat.
<img>Jalur Eksistensi</img>	Jalur Eksistensi	Entitas objek, antarmuka yang berinteraksi dan berkomunikasi.
<img>Input Pesan</img>	Input Pesan	Menceritakan interaksi antara item-item yang menyimpan detail tentang peristiwa yang terjadi.
<img>Message to Self</img>	Message to Self	Menjelaskan interaksi objek dengan pemanggilan metode dan nilai balik yang menentukan kejadian yang terjadi.
2.24 Pengujian BlackBox
Pengujian blackbox merupakan metode pengujian perangkat lunak yang berfokus pada pengujian fungsi sistem tanpa melihat atau menganalisis struktur internal maupun kode program di dalamnya. Pengujian ini dilakukan dengan memeriksa kesesuaian antara masukan yang diberikan dan keluaran yang dihasilkan berdasarkan spesifikasi dan kebutuhan yang telah ditetapkan. Oleh karena itu, metode ini sangat sesuai digunakan pada pengujian tingkat tinggi ketika detail implementasi sistem tidak diketahui oleh penguji. Dalam pelaksanaannya, Pengujian blackbox memanfaatkan berbagai teknik seperti partisi ekivalensi, analisis nilai batas, pengujian tabel keputusan, dan pengujian transisi keadaan untuk mengidentifikasi kesalahan secara efektif. Metode ini dapat diterapkan pada berbagai tahapan pengujian perangkat lunak, antara lain pengujian unit, integrasi, sistem, penerimaan, regresi, dan fungsional (Kirinuki dan Tanno, 2024).

Page 78
BAB III
METODOLOGI PENELITIAN
3.1 Metode Pengumpulan Data
Dalam penelitian ini, terdapat beberapa teknik pengumpulan data yang diterapkan, antara lain sebagai berikut:

3.1.1 Akuisisi Dataset Publik (Open Source)
Dataset sekunder diperoleh dari repositori terbuka yang kredibel untuk mendukung variasi data dalam penelitian ini. Fokus utama dari akuisisi ini adalah pada karakteristik visual dan keberagaman citra struk pembelian. Berikut adalah rincian dataset publik yang digunakan:

Dataset CORD-v2 Berdasarkan penelitian Park dkk., 2019, penelitian ini menggunakan versi publik dari dataset CORD yang terdiri dari 1.000 citra struk khusus kategori restoran di Indonesia. Citra pada dataset ini telah mengalami proses pengolahan di mana teks dan informasi selain daftar item serta informasi pembayaran telah dihilangkan atau dilakukan proses blurring. Hal ini menghasilkan dataset yang secara visual hanya menonjolkan bagian transaksi utama pada struk. Dataset ini diakses melalui repositori Oxen.ai.
Dataset SROIE v2 Dataset ini berasal dari kompetisi ICDAR 2019 on Scanned Receipt OCR and Information Extraction oleh Z. Huang dkk., 2019. Penelitian ini memanfaatkan 1.000 citra struk hasil pindaian (scanned receipts) sebagai basis data citra. Fokus penggunaan dataset ini adalah pada kualitas visual dokumen pindaian yang merepresentasikan format struk cetak standar, dan tersedia melalui platform Kaggle.
Dataset Nanonets Dikurasi oleh Mandal dkk., 2025 sebagai bagian dari platform IDPLeaderboard. Dataset ini digunakan sebagai referensi dalam evaluasi Intelligent Document Processing (IDP), khususnya pada kategori pengenalan
<page_number>68</page_number>

Page 79
<page_number>69</page_number>

informasi kunci atau Key Information Extraction (KIE) untuk struk pembelian. Data citra ini diakses melalui Hugging Face.

Dataset UniqueData Merupakan dataset OCR Receipts from Grocery Stores yang dikembangkan oleh UniData, 2026. Dataset ini berfokus pada deteksi teks pada struk toko kelontong (grocery stores) dengan kualitas citra yang dioptimalkan untuk pelatihan model AI di sektor ritel yang terdiri dari 20 citra. Dataset ini diperoleh melalui repositori Hugging Face.

Dataset Roboflow Bersumber dari repositori (Roboflow, 2024), dataset ini menyediakan koleksi citra struk belanja dengan karakteristik visual khusus berupa format grayscale (skala abu-abu) yang terdiri dari 1.719 citra. Penggunaan citra non-warna ini bertujuan untuk menguji performa model terhadap dokumen yang memiliki keterbatasan informasi kromatik (warna). Dataset ini diakses melalui platform Roboflow Universe.

Dataset ExpressExpense Dataset ini disediakan oleh ExpressExpense, 2026 melalui koleksi Sample Receipt Dataset (SRD). Data terdiri dari 200 citra struk restoran berkualitas tinggi dengan dimensi gambar yang tajam (lebih dari 600 piksel). Dataset ini digunakan untuk memperkaya variasi citra struk restoran dalam kondisi pencahayaan dan sudut pengambilan gambar yang ideal.

3.1.2 Pengumpulan Data Manual (Web Discovery) Peneliti melakukan pencarian dan pengumpulan citra struk pembelian secara manual melalui Google Images dengan kata kunci “struk pembelian” untuk mendapatkan sampel visual struk dengan kondisi dan format yang beragam. Pengumpulan ini juga mencakup platform media sosial X (Twitter) dan Threads, yang sering digunakan pengguna untuk berbagi foto struk pembelian dalam konteks percakapan sehari-hari. Metode ini bertujuan untuk menangkap variasi struk yang tidak terwakili dalam dataset publik, khususnya struk dari merchant Indonesia dengan format dan tipografi yang bervariasi.

Page 80
<page_number>70</page_number>

3.1.3 Web Scraping (Pinterest)

Untuk memperkaya variasi visual dataset, dilakukan proses web scraping pada platform Pinterest dengan menggunakan kata kunci pencarian “struk pembelian”. Platform ini dipilih karena menyediakan koleksi foto struk yang diambil secara langsung menggunakan kamera ponsel (handheld) dengan berbagai variasi sudut pengambilan gambar (angle) yang tidak beraturan. Secara khusus, pengumpulan data melalui metode ini difokuskan pada citra yang memiliki format vertikal atau rasio aspek 9:16, yang merepresentasikan perilaku pengguna saat mendokumentasikan struk secara fisik. Variasi kondisi gambar, seperti sudut kemiringan yang ekstrem, kondisi pencahayaan yang bervariasi, serta tingkat kejelasan teks yang berbeda-beda, sangat krusial untuk meningkatkan ketahanan (robustness) model terhadap input dokumen berkualitas rendah dalam skenario penggunaan nyata.

3.1.4 Pengambilan Data Primer (Real-Life)

Data primer dikumpulkan langsung oleh peneliti melalui dokumentasi struk pembelian nyata dari transaksi sehari-hari guna memastikan dataset mengandung sampel yang representatif terhadap kondisi penggunaan sistem sebenarnya di Indonesia. Koleksi data ini mencakup struk fisik dari minimarket, restoran, dan toko ritel lokal dengan berbagai format sistem kasir konvensional, serta menyertakan e-receipt atau bukti bayar digital dari berbagai platform belanja daring dan layanan transportasi online yang saat ini umum digunakan. Dalam proses dokumentasi struk fisik, peneliti menggunakan perangkat iPhone 13 Pro untuk menjamin ketajaman resolusi dan keterbacaan teks pada citra digital, sehingga seluruh data primer baik dalam format cetak maupun digital memiliki kualitas yang optimal untuk diolah pada tahap penelitian selanjutnya.

3.2 Metode Pengembangan Sistem

Dalam penelitian ini, digunakan metode pengembangan sistem Agile Scrum yang terdiri dari fase Pre-Game, Development (Sprint), dan Post-Game. Pemilihan Agile Scrum didasarkan pada sifat eksploratif penelitian ini, di mana komponen fine-tuning GLM-OCR, arsitektur Hierarchical Agent Teams, dan integrasi MCP

Page 81
<page_number>71</page_number>

memerlukan evaluasi iteratif dan penyesuaian berkelanjutan yang tidak dapat sepenuhnya direncanakan di awal. Berikut adalah rincian pelaksanaan setiap fase dalam konteks penelitian ini:

Pre-Game (Perencanaan) Pada fase ini dilakukan penyusunan kebutuhan sistem secara menyeluruh dan pembentukan product backlog. Aktivitas mencakup analisis kebutuhan fungsional dan non-fungsional sistem Agentic AI untuk data entry struk pembelian, penetapan arsitektur sistem secara high-level, penentuan komponen utama yang akan dikembangkan (GLM-OCR fine-tuning, LangGraph agent, MCP server, React Native frontend), serta prioritisasi item backlog berdasarkan dependensi teknis antar komponen.

Sprint 1 (Fine-Tuning dan Persiapan Data) Sprint pertama berfokus pada persiapan dataset fine-tuning dan pelatihan model GLM-OCR menggunakan LoRA via LLaMA Factory. Aktivitas mencakup pengumpulan dan anotasi dataset struk pembelian dari empat sumber (open-source, web discovery, scraping, dan data nyata), konfigurasi lingkungan pelatihan LLaMA Factory dengan parameter LoRA, pelaksanaan fine-tuning dengan target konsistensi output JSON schema, serta evaluasi awal hasil ekstraksi menggunakan metrik ANLS* dan KIEval.

Sprint 2 (Arsitektur Agentic dan MCP) Sprint kedua berfokus pada pembangunan arsitektur backend sistem. Aktivitas mencakup implementasi Hierarchical Agent Teams menggunakan LangGraph dengan supervisor agent, SQL agent, dan data entry team, implementasi MCP-SQLite dan MCP-GSheets beserta tool yang diperlukan, integrasi guardrails (Llama Guard 2 dan LLM-as-Judge), implementasi mekanisme HITL checkpoint sebelum operasi penulisan ke Google Sheets, serta evaluasi MCP tool accuracy mencakup AST dan Pass@K.

Sprint 3 (Frontend dan Integrasi Sistem) Sprint ketiga berfokus pada pengembangan antarmuka pengguna dan integrasi end-to-end seluruh komponen sistem. Aktivitas mencakup pengembangan antarmuka React Native dengan Expo untuk Android, iOS, dan Web, integrasi

Page 82
<page_number>72</page_number>

*frontend dengan backend FastAPI, pengujian alur kerja end-to-end dari input struk hingga output Google Sheets, serta penyesuaian berdasarkan hasil pengujian integrasi.

Post-Game (Pengujian dan Finalisasi)
Fase Post-Game mencakup pengujian sistem secara menyeluruh dan finalisasi dokumentasi. Aktivitas mencakup Black Box Testing terhadap seluruh fungsionalitas sistem, serta penyempurnaan sistem berdasarkan hasil evaluasi.

3.3 Waktu dan Tempat Penelitian

3.3.1 Waktu

Waktu pelaksanaan penelitian berlangsung dari bulan Februari 2026 sampai April 2026 dengan rincian yang ditampilkan pada Tabel 3.1.

Tabel 3. 1 Waktu penelitian

No	Detail Kegiatan	Waktu Penelitian (2026)	Keterangan
Februari	Maret	April
1	2	3	4	1	2	3	4	1	2	3	4
1	*Pre-Game* (Perencanaan & Backlog)													*Product Backlog*, *Arsitektur Sistem*
2	*Sprint 1* (*Fine Tuning* & *Dataset*)													*Dataset*, *LoRA*, *LLaMA Factory*, *KIEval*, *ANLS*
3	*Sprint 2* (*Agent* & *MCP*)													*LangGraph*, *MCP Server*, *Guardrails*, *AST*, *Pass@K*
4	*Sprint 3* (*Frontend* & *Integrasi*)													*React Native*, *Expo*, *Fast API*
5	*Post-Game* (Pengujian & Finalisasi)													*Blackbox Testing*, *Evaluasi*, *Dokumentasi*
Page 83
<page_number>73</page_number>

3.3.2 Tempat Penelitian
Penelitian tugas akhir ini bertempat di Laboratorium Computer Science & Artificial Intelligence, Jurusan Teknik Informatika, Fakultas Teknik, UniversitasHalu Oleo.

3.4 Analisis Kebutuhan Sistem
Analisis kebutuhan sistem bertujuan untuk menetapkan spesifikasi yang diperlukan mulai dari tahap pengembangan hingga implementasi sistem. Analisis tersebut mencakup kebutuhan fungsional, yang terdiri atas input, proses, dan output, serta kebutuhan nonfungsional yang meliputi perangkat keras (hardware) dan perangkat lunak (software).

3.4.1 Analisis Kebutuhan Fungsional
Analisis kebutuhan fungsional bertujuan untuk mengidentifikasi fitur-fitur yang harus tersedia agar sistem dapat beroperasi sesuai tujuan penelitian, yaitu mengotomatisasi proses data entry dari struk pembelian menggunakan Vision Language Model ter-fine-tune dan orkestrasi hierarchical multi-agent berbasis MCP. Kebutuhan fungsional dalam penelitian ini dijabarkan dalam tiga kategori, yaitu kebutuhan masukan, kebutuhan proses, dan kebutuhan keluaran.

Kebutuhan Masukan (Input)

Sistem menerima dua jenis masukan utama dari pengguna melalui antarmuka percakapan (chatbot). Jenis masukan pertama adalah dokumen struk pembelian dalam format citra digital (JPG, PNG) atau PDF, yang diunggah oleh pengguna melalui fitur attachment pada antarmuka chat. Dokumen tersebut dapat berupa foto struk fisik yang diambil menggunakan kamera ponsel, citra hasil pemindaian (scan), maupun e-receipt dalam format digital. Sistem mendukung pemrosesan dokumen PDF multi-halaman, di mana setiap halaman diperlakukan sebagai satu unit struk yang diproses secara independen. Jenis masukan kedua adalah pesan teks (text-only) yang dikirimkan oleh pengguna dalam mode percakapan, yang dapat berupa instruksi untuk melihat data hasil ekstraksi,

Page 84
<page_number>74</page_number>

permintaan untuk memasukkan data ke Google Sheets, klarifikasi terhadap hasil ekstraksi, atau pertanyaan terkait data yang telah tersimpan dalam sistem. Selain itu, pengguna juga memberikan masukan berupa konfirmasi atau koreksi pada checkpoint Human-in-the-Loop (HITL) sebelum operasi penulisan data dieksekusi.

Kebutuhan Proses (Process)

Sistem melaksanakan serangkaian proses yang saling terkoordinasi untuk mentransformasi masukan menjadi keluaran yang diharapkan. Proses pertama adalah validasi keamanan melalui lapisan guardrails yang terdiri dari dua komponen paralel, yaitu deteksi prompt injection dan jailbreaking menggunakan model Llama Prompt Guard 2, serta penyaringan domain yang dilarang (blacklist) menggunakan pendekatan LLM-as-Judge dengan model Gemini. Proses kedua adalah ekstraksi informasi kunci (Key Information Extraction) dari citra struk pembelian menggunakan model GLM-OCR 0,9B yang telah di-fine-tune dengan LoRA. Model ini menerima citra struk dan menghasilkan keluaran JSON terstruktur yang mencakup informasi toko (store name, location, contacts), daftar item beserta harga, serta ringkasan pembayaran (grand total, metode pembayaran, kembalian). Untuk dokumen PDF, setiap halaman dirender menjadi citra PNG pada resolusi 200 DPI sebelum diproses oleh model. Proses ketiga adalah penyimpanan hasil ekstraksi ke database SQLite sebagai single source of truth, yang mencakup metadata dokumen, data per halaman, dan riwayat percakapan. Proses keempat adalah orkestrasi oleh Supervisor Agent (Klaudia) yang menganalisis kebutuhan pengguna, mendelegasikan tugas ke sub-agent yang sesuai (SQL Agent untuk operasi database atau Data Entry Team untuk operasi Google Sheets), dan menyintesis hasil untuk dikembalikan kepada pengguna. Proses kelima adalah Human-in-the-Loop, yaitu konfirmasi dari pengguna sebelum Data Entry Team Agent melakukan penulisan data ke Google Sheets melalui MCP-GSheets. Proses keenam adalah operasi data entry otomatis ke Google Sheets, yang mencakup pembuatan sheet baru, penambahan baris data, dan pembaruan sel melalui tool yang diekspos oleh MCP-GSheets.

Page 85
<page_number>75</page_number>

Kebutuhan Keluaran (Output)
Sistem menghasilkan tiga jenis keluaran utama. Keluaran pertama adalah data terstruktur dalam format JSON yang tersimpan di database SQLite, mencakup hasil ekstraksi informasi kunci dari setiap halaman struk yang diproses. Keluaran kedua adalah data struk pembelian yang telah dientri secara otomatis ke Google Sheets, dengan struktur kolom yang sesuai dengan skema ekstraksi (informasi toko, daftar item, dan ringkasan pembayaran). Keluaran ketiga adalah respons percakapan dari Supervisor Agent Klaudia yang disampaikan melalui antarmuka chat, berupa ringkasan hasil pemrosesan, konfirmasi status data entry, jawaban atas pertanyaan pengguna, atau permintaan klarifikasi apabila terdapat ambiguitas dalam instruksi pengguna.

3.4.2 Analisis Kebutuhan Nonfungsional

Analisis Analisis kebutuhan nonfungsional meliputi evaluasi sumber daya dan lingkungan yang diperlukan untuk membangun sistem. Secara umum, kebutuhan ini terbagi menjadi kebutuhan perangkat keras (hardware) dan perangkat lunak (software), yang bertujuan memastikan sistem beroperasi efisien dan memenuhi standar yang ditetapkan.

Kebutuhan Perangkat Keras
Perancangan dan pembangunan sistem memerlukan perangkat keras sebagai media utama untuk implementasi dan operasional sistem agar berfungsi optimal. Rincian kebutuhan perangkat keras yang digunakan dalam pengembangan sistem ini tercantum pada Tabel 3.2:

Tabel 3. 2 Spesifikasi perangkat keras

No.	Nama Perangkat	Spesifikasi
1.	Laptop	Macbook Air M2, 2022
2.	Processor	Chip Apple M2 CPU 8-core dan GPU 8-core
3.	Memory	RAM 16 GB
4.	Hardisk	256 GB
5.	Monitor	Liquid retina 13.6 inch
6.	Smartphone	iPhone 13 Pro
7.	Kamera	Pro 12MP camera system
8.	GPU Fine-tuning	NVIDIA A100 (40 GB VRAM)
Page 86
<page_number>76</page_number>

9.	GPU Inference	NVIDIA L4 (24 GB VRAM)
Kebutuhan Perangkat Lunak
Perancangan sistem memerlukan perangkat lunak sebagai komponen utama untuk mendukung implementasi dan operasional sistem yang dikembangkan. Rincian kebutuhan perangkat lunak untuk sistem ini disajikan pada Tabel 3.3:

Tabel 3. 3 Spesifikasi Perangkat Lunak

No	Nama	Fungsi	Spesifikasi
1	MacOS	Sistem operasi pengembangan utama	Sequoia 15.6
2	Python	Bahasa pemrograman backend dan AI	Python 3.13
3	React Native & Expo	Framework pengembangan aplikasi mobile	-
4	FastAPI	Pembangunan web service API	FastAPI 0.115
5	Langchain	Framework pengelolaan rantai LLM	Langchain 0.3.20
6	LangGraph	Orkestrasi Multi-Agent System (MAS)	LangGraph 0.3.30
7	FastMCP	Implementasi MCP	FastMCP 0.5.0
8	LLaMA Factory	Alat fine-tuning model GLM-OCR	-
9.	Groq	Inference engine guardrails	Groq 0.9
10.	vLLM	Inference engine GLM-OCR secara lokal/server	-
9	Hugging Face	Repositori model dan dataset	Akses Publik
Page 87
<page_number>77</page_number>

10	Kaggle & Roboflow	Sumber akuisisi dataset sekunder	Akses Publik
11	Oxen.ai	*Versioning* dataset	Akses Publik
12	Github & Git	Sistem kontrol versi code	-
13	MlFlow	*Tracking metrics logs*	-
14	Optuna	*Hyperparameter search*	-
15	Label Studio	Alat anotasi dataset	Versi *Open Source*
16	Lightning AI	Infrastruktur GPU *cloud*	Akses Publik
17	Visual Studio Code	*Integrated Development Environment (IDE)*	-
18	Xcode	*Compiler emulator iOS*	-
19	Google Sheets	*Media output*	Layanan *Cloud*
20	SQLite	Basis data lokal sistem	SQLite 0.20.0
3.5 Analisis Perancangan Sistem
Perancangan sistem ini mencakup empat komponen utama, yaitu flowchart, Unified Modeling Language (UML), antarmuka pengguna (UI), dan skenario pengujian. Flowchart digunakan untuk menggambarkan alur logika dan proses utama dari masukan hingga keluaran. UML digunakan untuk memodelkan interaksi antar komponen sistem melalui diagram use case, activity, class, dan sequence. Perancangan antarmuka menggambarkan tampilan visual yang akan digunakan pengguna untuk berinteraksi dengan sistem. Skenario pengujian mendefinisikan prosedur evaluasi yang mencakup perhitungan metrik secara matematis dan pengujian fungsionalitas blackbox.

3.5.1 Flowchart
Flowchart sistem pada Gambar 3.1 menggambarkan alur kerja keseluruhan dari sistem pemrosesan struk berbasis agen yang dirancang dalam penelitian ini. Alur dimulai ketika pengguna mengirimkan permintaan melalui antarmuka percakapan, baik berupa pesan teks maupun dokumen lampiran. Sebelum permintaan tersebut diproses lebih lanjut, setiap masukan yang diterima diwajibkan

Page 88
<page_number>78</page_number>

melewati lapisan Guardrails terlebih dahulu. Lapisan ini menggunakan kombinasi Llama Prompt Guard 2 dan mekanisme LLM-as-judge untuk mendeteksi potensi ancaman seperti prompt injection, konten berbahaya, serta topik yang berada di luar cakupan sistem. Apabila permintaan tidak lolos validasi, sistem secara langsung mengembalikan pesan penolakan kepada pengguna tanpa meneruskan proses ke komponen berikutnya.

Setelah melewati lapisan guardrails, sistem melakukan pemeriksaan kondisi untuk menentukan jalur pemrosesan yang sesuai berdasarkan jenis masukan yang diterima. Apabila pengguna mengunggah dokumen berupa PDF atau gambar, sistem mengarahkan alur ke jalur pemrosesan dokumen di mana dokumen dikonversi menjadi format gambar PNG dengan resolusi 200 DPI, kemudian diubah ke dalam format base64 untuk dikirimkan ke Extraction Agent. Extraction Agent memanfaatkan model GLM-OCR yang telah disesuaikan melalui fine-tuning untuk mengekstraksi informasi struk secara langsung dalam bentuk JSON terstruktur. Hasil ekstraksi selanjutnya divalidasi dan digabungkan ke dalam skema baku yang telah ditentukan sebelumnya.

Dalam kondisi di mana pengguna meminta proses data entry ke Google Sheets, baik setelah pemrosesan dokumen maupun melalui permintaan teks eksplisit, sistem menerapkan mekanisme Human-in-the-Loop (HITL) sebagai langkah konfirmasi sebelum eksekusi penulisan data dilakukan. Supervisor Agent menampilkan pratinjau data yang akan dimasukkan dan meminta persetujuan eksplisit dari pengguna terlebih dahulu. Apabila pengguna menyetujui, tugas penulisan didelegasikan kepada Data Entry Team yang terdiri dari tiga sub-agen terkoordinasi, yaitu Read Agent, Sheet Agent, dan Write Agent, yang mengeksekusi operasi penulisan secara terstruktur melalui MCP-GSheets. Sebaliknya, apabila pengguna menolak atau memberikan koreksi terhadap data yang ditampilkan, sistem mengembalikan alur ke tahap perbaikan data sebelum proses konfirmasi diulang kembali. Pendekatan ini memastikan bahwa tidak ada data yang dituliskan ke Google Sheets tanpa validasi eksplisit dari pengguna, sehingga integritas data dapat terjaga sepanjang siklus operasional sistem. Gambar 3.1 menunjukkan visual alur flowchart bagaimana sistem Klaudia bekerja.

Page 89
<page_number>79</page_number>

flowchart TD
    A([User mengirim pesan]) --> B[Guardrails Layer (Llama Prompt Guard 2 + LLM-as-Judge)]
    B --> C{"Lolos guardrails?"}
    C -- Tidak --> D[Keputusan penolakan ke User]
    C -- Ya --> E{"Ada attachment?"}
    E -- Ya (dokumen) --> F[Konversi PDF/Image ke base64 PNG (200 DPI)]
    E -- Tidak (teks) --> G[Supervisor Agent (Klaudia) Analisis kebutuhan & context enrichment]
    F --> H[Extraction Agent:GLM-OCR Fine-Tuned (JSON Terstruktur)]
    H --> I[Validasi & merge ke EXTRACTI ON_SCHEMA]
    I --> J[Simpan hasil ekstraksi ke SQLite (pages table)]
    J --> K[User koreksi data]
    K -->|Ditolak/Koreksi| J
    G --> L{"Perlu data entry ke Google Sheets?"}
    L -- Ya --> M{HITL: User konfirmasi data?}
    L -- Tidak --> N[Generate respons percakapan ke User]
    M -->|Dikonfirmasi| O[Data Entry Team: Write via MCP-GSheets]
    M -->|Tidak| N
    O --> P[Data berhasil ditulis ke Google Sheets]
    P --> N
    N --> Q([Respons ke User])
Gambar 3. 1 Flowchart alur sistem utama Klaudia

Page 90
<page_number>80</page_number>

3.5.2 Perancangan Unified Modeling Language (UML)

Sistem ini dirancang menggunakan Unified Modeling Language (UML), sebuah bahasa visual yang digunakan untuk memodelkan dan mengkomunikasikan suatu sistem melalui berbagai diagram. Empat jenis diagram UML yang digunakan dalam perancangan sistem ini meliputi use case diagram, activity diagram, class diagram, dan sequence diagram.

Use Case Diagram

Use case diagram menggambarkan interaksi antara aktor User (pengguna) dengan sistem Klaudia. Dalam diagram ini, batas sistem (system boundary) Klaudia terbagi menjadi dua kelompok use case.

Kelompok pertama adalah User Cases yang merepresentasikan enam fungsi yang dapat diakses langsung oleh pengguna, yaitu upload struk pembelian dalam format PDF atau citra, kirim pesan teks sebagai instruksi atau pertanyaan, lihat hasil ekstraksi struk yang telah diproses, minta data entry ke Google Sheets, konfirmasi atau koreksi data pada checkpoint Human-in-the-Loop (HITL), serta kelola sesi percakapan.

Kelompok kedua adalah Internal Process yang merepresentasikan lima proses otonom yang dieksekusi oleh sistem tanpa intervensi langsung pengguna, yaitu validasi guardrails untuk menyaring masukan yang tidak aman, ekstraksi KIE menggunakan GLM-OCR fine-tuned, orkestrasi agent oleh Supervisor Klaudia, context enrichment untuk menginjeksi informasi file aktif ke dalam konteks percakapan, query database melalui MCP-SQLite, serta tulis ke spreadsheet melalui MCP-GSheets. Hubungan antar kedua kelompok direpresentasikan melalui relasi include dan extend, di mana setiap use case pengguna memicu satu atau lebih proses internal secara otomatis. Use case diagram sistem Klaudia dapat dilihat pada Gambar 3.2.

Page 91
<page_number>81</page_number>

graph TD
    subgraph SISTEM KLAUDIA
        subgraph USER CASES
            A[Lihat hasil ekstraksi struk]
            B[Kelola sesi percakapan]
            C[Kirim pesan teks]
            D[Upload struk (PDF/Image)]
            E[Konfirmasi / koreksi (HITL)]
            F[Minta data entry GSheets]
        end

        subgraph INTERNAL PROCESS
            G[Orkestrasi agent]
            H[Context enrichment]
            I[Validasi guardrails]
            J[Ekstraksi KIE]
            K[Tulis ke spreadsheet]
            L[Query database]
        end

        User --> A
        User --> B
        User --> C
        User --> D
        User --> E
        User --> F

        A -- <<include>> --> G
        B -- <<include>> --> G
        C -- <<include>> --> H
        D -- <<include>> --> H
        E -- <<include>> --> I
        F -- <<include>> --> J

        G -- <<extend>> --> L
        H -- <<extend>> --> L
        I -- <<extend>> --> L
        J -- <<extend>> --> L
        K -- <<extend>> --> L
Gambar 3. 2 Use case diagram sistem Klaudia

Activity Diagram
Activity diagram menggambarkan alur aktivitas dari sisi pengguna dan sistem secara bersamaan menggunakan swimlane. Diagram ini dibagi menjadi dua bagian untuk mengakomodasi kompleksitas alur kerja sistem secara keseluruhan.

Bagian pertama merepresentasikan proses validasi masukan dan guardrails dengan dua swimlane, yaitu Pengguna dan Backend. Alur dimulai dari pengguna yang mengunggah struk atau mengirim pesan, kemudian FastAPI menerima request dan menjalankan lapisan guardrails. Pada tahap ini, dua komponen validasi dieksekusi secara paralel melalui mekanisme fork, yaitu Llama Prompt Guard 2 untuk deteksi prompt injection dan LLM-as-Judge untuk penyaringan domain yang dilarang. Kedua hasil validasi disinkronisasi melalui join, kemudian decision node menentukan apakah masukan aman atau tidak. Apabila tidak aman, pesan penolakan dikembalikan ke pengguna dan alur berakhir. Apabila aman, alur dilanjutkan ke proses routing dan ekstraksi. Alur proses validasi masukan dan guardrails ditunjukkan pada Gambar 3.3.

Page 92
<page_number>82</page_number>

flowchart TD
    subgraph Pengguna
        A(( )) --> B[User mengunggah struk / mengirim pesan]
    end

    subgraph Backend
        C[FastAPI menerima request] --> D[Jalankan Guardrails]
        D --> E[Llama Prompt Guard 2]
        D --> F[LLM-as-Judge (Blacklist Domain)]
        G{Aman?} -->|Tidak aman| H[Tolak & kembalikan pesan error]
        E --> G
        F --> G
        G -->|Aman| I[Routing & Ekstrasi]
        H --> J((( )))
    end
Gambat 3. 3 Activity diagram proses validasi masukan dan guardrails

Bagian kedua merepresentasikan proses routing, ekstraksi, orkestrasi agent, dan data entry dengan tiga swimlane, yaitu Pengguna, Backend, dan Klaudia. Alur dimulai dari masukan yang telah tervalidasi aman, kemudian decision node menentukan apakah terdapat attachment dokumen atau hanya pesan teks. Apabila terdapat attachment, citra dikonversi ke format base64 PNG dan diproses oleh GLM-OCR untuk menghasilkan JSON terstruktur yang disimpan ke SQLite. Apabila hanya pesan teks, alur langsung menuju context enrichment. Selanjutnya, Supervisor Agent menganalisis intent pengguna dan mendelegasikan tugas ke SQL Agent untuk query data atau menampilkan pratinjau data kepada pengguna untuk konfirmasi HITL. Apabila pengguna mengonfirmasi, Data Entry Team yang terdiri dari Read Agent, Sheet Agent, dan Write Agent mengeksekusi operasi penulisan ke Google Sheets melalui MCP-GSheets. Apabila pengguna mengoreksi data, alur

Page 93
<page_number>83</page_number>

kembali ke pratinjau hingga konfirmasi diperoleh. Alur proses routing, ekstraksi, dan orkestrasi data entry ditunjukkan pada Gambar 3.4.

flowchart TD
    subgraph Pengguna
    A(( )) --> B[User mengunggah struk / mengirim pesan]
    B --> C[Tampilkan pratinjau data ke User]
    C --> D[User meninjau hasil ekstraksi]
    D --> E{"Setuju?"}
    E -- Tidak --> F[User mengoreksi data]
    F --> G[User menerima konfirmasi data entry]
    G --> H((( )))
    end

    subgraph Backend
    I[Input Aman Tervalidasi] --> J{Ada attachment?}
    J -- Ada attachment --> K[Konversi PDF/ Image: base64 PNG]
    J -- Teks saja --> L[Context enrichment: inject file info]
    K --> M[GLM-OCR: JSON extraction]
    M --> N[Validasi schema & simpan ke SQLite]
    N --> L
    L --> O[Analisis intent pengguna]
    O --> P{Delegasi ke?}
    P -- Ya --> Q[Read Agent: cek spreadsheet]
    P -- Tidak --> C
    Q --> R[Sheet Agent: buat sheet baru]
    R --> S[Write Agent: append rows via MCP-GSheets]
    S --> T[SQL Agent: query MCP-SQLite]
    T --> U[Konfirmasi berhasil ke Supervisor]
    U --> G
    end

    subgraph Kludia
    J --> K
    O --> P
    T --> U
    end
Gambar 3. 4 Activity diagram proses routing, ekstraksi, dan orkestrasi data entry

Page 94
<page_number>84</page_number>

Class Diagram
Class diagram menggambarkan struktur statis sistem dengan menampilkan kelas-kelas utama beserta atribut, operasi, dan hubungan antar kelas. Diagram ini dibagi menjadi tiga bagian berdasarkan domain tanggung jawab masing-masing kelompok kelas.

Bagian pertama menggambarkan model data pengguna dan dokumen yang tersimpan dalam database SQLite. Kelas User memiliki relasi komposisi satu-ke-banyak terhadap kelas Session, di mana setiap sesi mengandung beberapa Conversation dan dapat mereferensikan satu atau lebih MetadataFile. Setiap MetadataFile terdiri dari satu atau lebih Page yang menyimpan hasil ekstraksi dalam format JSON. Kelas ExtractionAgent memiliki relasi dependensi terhadap MetadataFile dan Page, karena agent ini memproses dokumen dan memperbarui data halaman hasil ekstraksi. Class diagram model data pengguna dan dokumen ditunjukkan pada Gambar 3.5.

<img>Class diagram showing classes User, Session, Conversation, MetadataFile, Page, ExtractionAgent with their attributes, operations, and relationships.</img>

Gambar 3. 5 Class diagram model data pengguna dan dokumen

Page 95
<page_number>85</page_number>

Bagian kedua menggambarkan komponen guardrails yang bertanggung jawab atas validasi keamanan masukan. Kelas GuardrailsLayer memiliki relasi komposisi terhadap dua kelas pelaksana, yaitu PromptGuardDetector yang mendeteksi prompt injection dan jailbreaking, serta BlacklistJudge yang mengevaluasi apakah masukan termasuk domain yang dilarang. Kedua komponen dieksekusi secara paralel oleh GuardrailsLayer. Class diagram komponen guardrails ditunjukkan pada Gambar 3.6.

classDiagram
    class GuardrailsLayer {
        + validate(messageText: String): Boolean
    }
    class PromptGuardDetector {
        - String modelName
        + detect(text: String): Boolean
    }
    class BlacklistJudge {
        - String llmModel
        - List<String> domains
        + evaluate(text: String): Boolean
    }
    GuardrailsLayer "1" -- "1" PromptGuardDetector : executes
    GuardrailsLayer "1" -- "1" BlacklistJudge : executes
Gambar 3. 6 Class diagram komponen guardrails

Bagian ketiga menggambarkan hierarki agent dan integrasi MCP server. Kelas SupervisorAgent mengorkestrasikan SQLAgent dan DataEntryTeam melalui pola Hierarchical Agent Teams pada LangGraph. DataEntryTeam memiliki relasi komposisi terhadap tiga sub-agent spesialis, yaitu ReadAgent untuk pembacaan data spreadsheet, SheetAgent untuk pengelolaan tab sheet, dan WriteAgent untuk operasi penulisan data. SQLAgent mengeksekusi tool melalui MCPSQLite, sedangkan DataEntryTeam mengeksekusi tool melalui MCPGSheets, di mana relasi tool execution merepresentasikan batas eksekusi agent-tool yang distandarkan oleh Model Context Protocol. Class diagram hierarki agent dan MCP server ditunjukkan pada Gambar 3.7.

Page 96
<page_number>86</page_number>

classDiagram
    class SupervisorAgent {
        - String llmModel
        - String persona
        + analyzeIntent(text: String)
        + delegateTask(task: String)
    }
    class DataEntryTeam {
        - Object mcpGSheetsClient
        + coordinateTeam()
    }
    class ReadAgent {
        + listSheets()
        + getSpreadsheetInfo()
    }
    class WriteAgent {
        + updateCells(range: String, values: List)
        + appendRows(sheetId: String, data: List)
    }
    class SheetAgent {
        + createSheet(name: String)
        + deleteSheet(id: String)
    }
    class MCPSheets {
        - Integer port
        - String credentialsPath
        + callSheetAPI(endpoint: String)
    }
    class MCPSQLite {
        - Integer port
        - String dbPath
        + executeQuery(sql: String)
    }
    class SQLAgent {
        - Object mcpSqliteClient
        + getDocument(docId: Integer)
        + listPages(docId: Integer)
    }

    SupervisorAgent "1" -- "1" DataEntryTeam : orchestrates
    DataEntryTeam "1" -- "1" MCPSheets : tool_execution
    MCPSheets "1" -- "1" ReadAgent : manages
    MCPSheets "1" -- "1" WriteAgent : manages
    MCPSheets "1" -- "1" SheetAgent : manages
    MCPSQLite "1" -- "1" SQLAgent : tool_execution
Gambar 3.7 Class diagram hierarki agent dan MCP server

Sequence Diagram
Sequence diagram menggambarkan interaksi antar objek serta pertukaran pesan secara kronologis untuk skenario utama sistem. Diagram ini dibagi menjadi tiga bagian yang merepresentasikan tiga fase utama dalam alur kerja end-to-end.

Bagian pertama menggambarkan fase upload dokumen dan ekstraksi informasi. Alur dimulai dari pengguna yang mengunggah struk melalui frontend React Native, kemudian FastAPI menerima request dalam format multipart yang berisi file dokumen beserta pesan teks, dan meneruskan masukan ke lapisan Guardrails untuk validasi keamanan. Setelah masukan dinyatakan aman oleh kedua komponen guardrails yang berjalan secara paralel, Extraction Agent menerima dokumen dan melakukan konversi ke format base64 PNG pada resolusi 200 DPI apabila dokumen berupa PDF multi-halaman. Citra yang telah dikonversi dikirimkan ke GLM-OCR melalui endpoint vLLM beserta prompt skema JSON, dan model menghasilkan keluaran JSON terstruktur yang mencakup informasi

Page 97
<page_number>87</page_number>

toko, daftar item, serta ringkasan pembayaran. Hasil ekstraksi kemudian divalidasi terhadap skema yang telah didefinisikan, di mana field yang hilang diisi dengan nilai default (string kosong untuk teks, array kosong untuk daftar), dan data yang telah tervalidasi disimpan ke tabel pages pada database SQLite beserta pembaruan status pada tabel metadata_file. Supervisor Agent selanjutnya menerima konteks file yang diinjeksikan ke dalam system prompt melalui mekanisme context enrichment, dan menghasilkan respons ringkasan hasil pemrosesan yang di-stream kepada pengguna melalui antarmuka percakapan. Sequence diagram fase upload dan ekstraksi ditunjukkan pada Gambar 3.8.

sequenceDiagram;
    participant User;
    participant FastAPI;
    participant Guardrails;
    participant Extraction Agent;
    participant GLM-OCR (vLLM);
    participant SQLiteDB;
    participant Supervisor;
    User->>FastAPI: Upload struk (PDF/image) + pesan;
    FastAPI->>Guardrails: Validasi (Prompt Guard + LLM Judge);
    Guardrails-->>FastAPI: PASS;
    FastAPI->>Extraction Agent: process_document(file, metadata_id);
    Extraction Agent->>GLM-OCR (vLLM): POST image + JSON schema prompt;
    GLM-OCR (vLLM)-->>Extraction Agent: Structured JSON;
    Extraction Agent->>SQLiteDB: INSERT pages + UPDATE metadata_file;
    SQLiteDB-->>Extraction Agent: (status: success, pages: n);
    Extraction Agent->>Supervisor: Invoke + inject file context;
    Supervisor->>Extraction Agent: "Struk diproses! n item ditemukan.";
    Supervisor->>User: Stream response;
Gambar 3. 8 Sequence diagram proses upload struk hingga data entry ke Google Sheets

Bagian kedua menggambarkan fase permintaan data entry dan konfirmasi HITL. Pengguna mengirimkan instruksi berupa pesan teks untuk memasukkan data hasil ekstraksi ke Google Sheets, yang setelah melewati validasi guardrails, diteruskan ke Supervisor Agent melalui mekanisme invoke pada graf LangGraph. Supervisor menganalisis intent pengguna dan mendelegasikan pengambilan data ke SQL Agent, yang memanggil tool get_extraction melalui MCP-SQLite untuk mengambil JSON hasil ekstraksi dari tabel pages berdasarkan page_id yang direferensikan. Data yang diperoleh dikembalikan ke Supervisor, yang kemudian

Page 98
<page_number>88</page_number>

memformat data tersebut menjadi tabel pratinjau yang mudah dibaca oleh pengguna, mencakup kolom-kolom seperti nama item, kuantitas, harga satuan, dan total harga. Mekanisme interrupt pada LangGraph diaktifkan pada titik ini, yang menghentikan sementara eksekusi graf dan mengirimkan pratinjau data beserta permintaan konfirmasi kepada pengguna sebelum operasi penulisan yang bersifat irreversible dilaksanakan. Pendekatan ini memastikan bahwa tidak ada data yang ditulis ke Google Sheets tanpa persetujuan eksplisit dari pengguna, sesuai dengan prinsip Human-in-the-Loop yang diterapkan dalam arsitektur sistem. Sequence diagram fase permintaan data entry dan HITL ditunjukkan pada Gambar 3.9.

graph TD A[User] -->|Masukkan data ke Google Sheets| B[FastAPI] B -->|Validasi input| C[Guardrails] C -->|PASS| D[Supervisor] D -->|Invoke graph| E[SQLAgent] E --> F[SQLiteDB]
subgraph User Interface
    G[User]
    H[Tampilkan pratinjau + tombol konfirmasi]
    G --> H
end

subgraph FastAPI
    I[FastAPI]
    J[Validasi input]
    K[PASS]
    L[Invoke graph]
    I --> J
    J --> K
    K --> L
end

subgraph Guardrails
    M[Guardrails]
    N[Validasi input]
    O[PASS]
    M --> N
    N --> O
end

subgraph Supervisor
    P[Supervisor]
    Q[Delegasi: ambil data ekstraksi]
    R[get_extraction(page_id=1)]
    S[extraction JSON]
    T[Return data]
    P --> Q
    Q --> R
    R --> S
    S --> T
end

subgraph SQL Agent
    U[SQLAgent]
    V[Return data]
    U --> V
end

subgraph SQLite Database
    W[SQLiteDB]
    X[Return data]
    Y[Return data]
    Z[Return data]
    W --> X
    X --> Y
    Y --> Z
end

subgraph Sequence Diagram
    A -- "Masukkan data ke Google Sheets" --> B
    B -- "Validasi input" --> C
    C -- "PASS" --> D
    D -- "Invoke graph" --> E
    E -- "Delegasi: ambil data ekstraksi" --> F
    F -- "get_extraction(page_id=1)" --> G
    G -- "extraction JSON" --> H
    H -- "Return data" --> I
    I -- "Return data" --> J
    J -- "Return data" --> K
    K -- "Return data" --> L
    L -- "Return data" --> M
    M -- "Return data" --> N
    N -- "Return data" --> O
    O -- "Return data" --> P
    P -- "Return data" --> Q
    Q -- "Return data" --> R
    R -- "Return data" --> S
    S -- "Return data" --> T
    T -- "Return data" --> U
    U -- "Return data" --> V
    V -- "Return data" --> W
    W -- "Return data" --> X
    X -- "Return data" --> Y
    Y -- "Return data" --> Z
end
Gambart 3. 9 Sequence diagram fase permintaan data entry dan HITL

Bagian ketiga menggambarkan fase konfirmasi pengguna dan penulisan data ke Google Sheets. Setelah pengguna mengonfirmasi, Supervisor Agent melanjutkan eksekusi graf dari titik interrupt dan mendelegasikan tugas penulisan ke Data Entry Team. Tim ini secara berurutan memanggil tool MCP-GSheets untuk memeriksa daftar sheet yang tersedia, membuat tab sheet baru apabila diperlukan, dan menambahkan baris data hasil ekstraksi. Konfirmasi keberhasilan dikembalikan melalui Supervisor ke pengguna. Sequence diagram fase konfirmasi dan penulisan ke Google Sheets ditunjukkan pada Gambar 3.10.

Page 99
<page_number>89</page_number>

sequenceDiagram;
    participant User;
    participant FastAPI;
    participant Supervisor;
    participant Data Entry Team;
    participant MCP-GSheets;
    participant Google Sheets;
    User->>FastAPI: "Ya, konfirmasi";
    FastAPI->>Supervisor: -- Resume dari interrupt point ->;
    Supervisor->>Data Entry Team: -- Delegasi: tulis ke Sheets ->;
    Data Entry Team->>MCP-GSheets: -- list_sheets(spreadsheet_id) ->;
    MCP-GSheets->>Google Sheets: GET metadata ->;
    Google Sheets<-- MCP-GSheets: (sheets: n);
    MCP-GSheets->>Google Sheets: create_sheet("Store_A") ->;
    Google Sheets->>MCP-GSheets: POST batchUpdate ->;
    MCP-GSheets->>Google Sheets: append_rows(values) ->;
    Google Sheets<-- MCP-GSheets: (updatedRows: n);
    Supervisor->>User: -- n baris berhasil ->;
    User->>User: "Data berhasil ditulis ke 'Indomaret' ✓";
Gambar 3. 10 Sequence diagram fase konfirmasi dan penulisan ke Google Sheets

3.5.3 Perancangan Antarmuka
Antarmuka pengguna sistem Klaudia dirancang menggunakan React Native dengan Expo sebagai framework pengembangan lintas platform, dengan fokus implementasi pada versi mobile iOS. Pemilihan platform iOS didasarkan pada kesesuaian dengan perangkat yang digunakan selama proses penelitian, yaitu MacBook Air M2 sebagai lingkungan pengembangan utama dan iPhone 13 Pro sebagai perangkat pengambilan data primer berupa foto struk pembelian, yang menjamin konsistensi antara perangkat pengembangan, pengujian, dan pengambilan data dalam satu ekosistem. Antarmuka terdiri dari tiga halaman utama yang dapat diakses melalui navigasi tab bar di bagian bawah layar. Halaman pertama adalah AI Chat, yang berfungsi sebagai antarmuka percakapan utama antara pengguna dan Supervisor Agent Klaudia. Halaman ini menampilkan bubble pesan dari pengguna dan respons Klaudia, mendukung pengunggahan citra struk melalui tombol attachment, serta menampilkan ringkasan hasil ekstraksi dan

Page 100
<page_number>90</page_number>

konfirmasi Human-in-the-Loop secara langsung di dalam alur percakapan. Halaman kedua adalah Laporan Struk, yang menampilkan WebView berbasis Expo React Native yang terhubung secara real-time dengan Google Sheets, memungkinkan pengguna memantau dan memverifikasi data struk yang telah dientri oleh Data Entry Team Agent tanpa perlu berpindah ke aplikasi Google Sheets secara terpisah. Halaman ketiga adalah Profile, yang menyediakan informasi akun pengguna, pengaturan sistem, keamanan akun, serta riwayat aktivitas.

Perancangan visual antarmuka mengadopsi skema warna gelap (dark theme) yang memberikan kenyamanan visual pada penggunaan dalam berbagai kondisi pencahayaan, khususnya saat pengguna memfoto struk di lingkungan ritel yang umumnya memiliki pencahayaan bervariasi. Rancangan antarmuka pengguna sistem Klaudia pada platform mobile iOS ditunjukkan pada Gambar 3.10.

iPhone 15 Pro - Chat Page <img>iPhone 15 Pro - Chat Page screenshot showing AI Chat interface with messages about processing receipts.</img>

iPhone 15 Pro - Google Sheet Page <img>iPhone 15 Pro - Google Sheet Page screenshot showing a spreadsheet titled "Data Ekstraksi Alfamart" with columns ID, Tanggal, Toko, Barang, Qty, Harga Satuan, Total Harga, and rows of transaction data.</img>

iPhone 15 Pro - Profile <img>iPhone 15 Pro - Profile screenshot showing user profile page with a circular profile picture, name "Ryuuky", email "ryuuky@gmail.com", settings icon, account security indicator, activity history, contact us, and privacy policy options.</img>

Gambar 3. 11 Rancangan antarmuka pengguna sistem Klaudia

3.5.4 Skenario Perancangan & Pengujuan Sistem
Skenario pengujian sistem dirancang untuk mengevaluasi kinerja secara end-to-end, mulai dari masukan berupa citra struk pembelian hingga keluaran berupa data yang tertulis di Google Sheets. Evaluasi dilakukan dalam dua tahap

Page 101
<page_number>91</page_number>

utama: evaluasi kualitas ekstraksi informasi dan evaluasi kinerja orkestrasi agent. Pada setiap tahap, perhitungan matematis dilakukan secara manual berdasarkan rumus yang telah didefinisikan pada Bab II untuk memverifikasi kebenaran implementasi metrik.

A. Skenario Fine-Tuning GLM-OCR dengan LoRA

Proses fine-tuning dilakukan menggunakan LLaMA Factory dengan konfigurasi LoRA pada model GLM-OCR 0,9B. Parameter LoRA yang digunakan mencakup rank r = 8, learning rate 1×10⁻⁴, dan target module = all (seluruh lapisan linear). Dengan dimensi model d = 896 (dimensi tersebunyi GLM-0.5B decoder), jumlah parameter yang dapat dilatih pada satu lapisan LoRA dihitung sebagai berikut.

Matriks dekomposisi low-rank terdiri dari A ∈ R^(r×k) dan B ∈ R^(d×r), di mana r = 8 dan d = k = 896. Jumlah parameter trainable per lapisan:

Parameter(_{LoRA}) = r × k + d × r = 8 × 896 + 896 × 8 = 14.336 parameter

Sebagai perbandingan, full fine-tuning pada lapisan yang sama memerlukan d × k = 896 × 896 = 802.816 parameter. Rasio efisiensi parameter LoRA terhadap full fine-tuning pada satu lapisan adalah:

Rasio = 14.336 / 802.816 ≈ 0,0179 ≈ 1,79

Efisiensi ini menunjukkan bahwa LoRA hanya memodifikasi sekitar 1,79% parameter per lapisan dibandingkan full fine-tuning, yang memungkinkan pelatihan pada perangkat dengan memori GPU terbatas (≥ 8 GB VRAM).

Dataset pelatihan terdiri dari 800 pasangan citra-label untuk training dan 100 untuk testing, yang dikumpulkan dari delapan sumber dataset. Pelatihan dilakukan selama 3 epoch dengan batch size efektif 16 (per_device_batch_size = 4 × gradient_accumulation_steps = 4) menggunakan cosine learning rate scheduler dengan warmup ratio 0,1.

B. Skenario Evaluasi Kualitas Ekstraksi

B.1. Perhitungan Manual KIEval

Misalkan satu struk belanja Indomaret memiliki ground truth berikut:

Page 102
<page_number>92</page_number>

Ground Truth (GT):

Grup 0 (non-grup): store_name = "INDOMARET", payment_date = "30/01/2025"
Grup 1 (item): item_name = "INDOMIE GORENG", quantity = "2", unit_price = "3.500", total_price = "7.000"
Grup 2 (item): item_name = "AQUA 600ML", quantity = "1", unit_price = "4.000", total_price = "4.000"
Prediksi Model (PR):

Grup 0 (non-grup): store_name = "INDOMARET", payment_date = "30/01/2025"
Grup 1 (item): item_name = "INDOMIE GORENG", quantity = "2", unit_price = "3.500", total_price = "7.000"
Grup 2 (item): item_name = "AQUA 600ML", quantity = "1", unit_price = "4.000", total_price = "4.500" ← salah
Langkah 1 (Group Matching dengan Hungarian Algorithm): Skor pencocokan S(n,m) dihitung sebagai jumlah entitas identik:

S(0,0) = 2 (store_name cocok, payment_date cocok)
S(1,1) = 4 (semua entitas item 1 cocok)
S(2,2) = 3 (item_name, quantity, unit_price cocok; total_price tidak cocok)
Hasil Hungarian matching: G = {(0,0), (1,1), (2,2)} – semua grup berhasil dipasangkan.

Langkah 2 (Hitung TP, FN, FP per pasangan):

Pasangan (0,0): TP = 2, FN = 0, FP = 0
Pasangan (1,1): TP = 4, FN = 0, FP = 0
Pasangan (2,2): TP = 3, FN = 1 (total_price GT tidak cocok), FP = 1 (total_price PR salah)
Langkah 3 (Akumulasi statistik): TPentity = 2 + 4 + 3 = 9 FNentity = 0 + 0 + 1 = 1 FPentity = 0 + 0 + 1 = 1

Page 103
<page_number>93</page_number>

Langkah 4 (Hitung KIEval Entity F1):

Precision = TP/(TP + FP) = 9/(9 + 1) = 0,900

Recall = TP/(TP + FN) = 9/(9 + 1) = 0,900

KIEvalEntityF1 = 2 × (0,900 × 0,900)/(0,900 + 0,900) = 0,900

Langkah 5 (Hitung KIEval Group F1):

G' = G (0,0) = (1,1), (2,2) hanya grup item yang dievaluasi.

Pasangan (1,1): Semua entitas identik → TP_group = 1
Pasangan (2,2): total_price berbeda → bukan TP_group
TPgroup = 1, FNgroup = 0, FPgroup = 0 (semua punya pasangan, hanya 1 yang tidak perfect).

Total grup GT = 2, total perfect match = 1

KIEval Group F1: Precision = 1/2 = 0,500; Recall = 1/2 = 0,500

KIEval Group F1 = 2 × (0,5 × 0,5) / (0,5 + 0,5) = 0,500

Interpretasinya, model berhasil mengekstrak 9 dari 10 entitas dengan benar (Entity F1 = 0,900), namun hanya 1 dari 2 grup item yang seluruh entitasnya cocok secara sempurna (Group F1 = 0,500). Kesalahan pada total_price item kedua menunjukkan kebutuhan perbaikan pada kemampuan model dalam membaca angka yang berdekatan.

B.2. Perhitungan Manual ANLS*

Menggunakan contoh yang sama, dihitung ANLS* untuk field total_price item kedua (AQUA 600ML):

Ground truth (g): "4.000" Prediksi (p): "4.500"

Langkah 1 (Hitung Levenshtein Distance (LD)):

LD("4.000", "4.500") = 2 (substitusi: '0'→'5' pada posisi 2, dan '0'→'0' sudah cocok, sebenarnya hanya 1 substitusi karakter)

Koreksi: perbandingan karakter per karakter:

"4" = "4" ✓
"." = "." ✓
"0" ≠ "5" → substitusi (1)
"0" = "0" ✓
Page 104
<page_number>94</page_number>

"0" = "0" ✓
LD("4.000", "4.500") = 1

Langkah 2 (Hitung Normalized Levenshtein Distance (NLD)):

NLD = LD/max(|g|, |p|) = 1/max(5,5) = 1/5 = 0,200

Langkah 3 (Cek ambang batas (τ = 0,5)):

Karena NLD = 0,200 < τ = 0,5 → skor dihitung.

Langkah 4 (Hitung skor s untuk field ini):

s(g, p) = 1,0 − NLD = 1,0 − 0,200 = 0,800

Langkah 5 (Hitung ANLS* keseluruhan untuk satu struk):

Misalkan terdapat 10 field pada struk. Sembilan field memiliki skor 1,0 (cocok sempurna) dan satu field (total_price AQUA) memiliki skor 0,800.

ANLS *= (9 × 1,0 + 1 × 0,800)/10 = 9,800/10 = 0,980

Interpretasi: Skor ANLS* = 0,980 menunjukkan keluaran JSON yang sangat mendekati ground truth secara keseluruhan, dengan sedikit deviasi pada satu field numerik.

C. Skenario Evaluasi Kinerja Orkestrasi Agent

C.1. Perhitungan Manual AST Accuracy

Merujuk pada rumus AST accuracy pada Persamaan (2.30)-(2.32) di Bab II, dilakukan perhitungan manual untuk pemrosesan struk.

Kasus 1 (Ada Kesalahan Prediksi):

Satu test case memproses struk Indomaret. Supervisor Agent (Klaudia) harus mengambil data ekstraksi dari SQLite terlebih dahulu via MCP-SQL, lalu menuliskannya ke Google Sheets via MCP-GSheets. Ground truth mewajibkan 4 tool dipanggil secara berurutan.

Tabel 3. 4 Kasus 1 AST akurasi

Tool	Komponen	Ground Truth	Prediksi Agent	Match
get_document	function	get_document	get_document	✓
req. param	metadata_file_id	metadata_file_id	✓
type & value	metadata_file_id=1	metadata_file_id=1	✓
Page 105
<page_number>95</page_number>

get_
extraction	function	get_extraction	get_extraction	☑
req. param	page_id	page_id	☑
type &
value	page_id=1	page_id=1	☑
list_
sheets	function	list_sheets	list_sheets	☑
req. param	spreadsheet_id	spreadsheet_id	☑
type &
value	spreadsheet_id="a
bc"	spreadsheet_id="xyz
"	☒
append_
rows	function	append_rows	append_rows	☑
req. param	spreadsheet_id,
range, values	spreadsheet_id,
range, values	☑
type &
value	range=
"Indomaret!A:H"	range=
"Alfamart!A:H"	☒
Perhitungan ASTi per tool (M = 4):

AST1 = 1 ∧ 1 ∧ 1 = 1,00 AST2 = 1 ∧ 1 ∧ 1 = 1,00 AST3 = 1 ∧ 1 ∧ 0 = 0,00 AST4 = 1 ∧ 1 ∧ 0 = 0,00

AST_AccuracyCase 1 = 1/4 (1,00 + 1,00 + 0,00 + 0,00) = 2,00 / 4 = 0,50

Interpretasinya agent memanggil2 tool pertama dengan benar, namun membuat kesalahan pada nilai parameter di 2 tool terakhir, spreadsheet_id salah saat list_sheets dan range mengarah ke sheet generik "Alfamart" bukan sheet spesifik "Indomaret". Karena evaluasi bersifat all-or-nothing, skor kedua tool tersebut jatuh menjadi 0, sehingga akurasi keseluruhan test case ini adalah 0,50.

Kasus 2 (Prediksi Sempurna):

Satu test case memproses struk Alfamart. Agent memanggil 4 tool dengan nama fungsi, parameter wajib, serta nilai parameter yang seluruhnya sesuai ground truth.

Page 106
<page_number>96</page_number>

Tabel 3.5 Kasus 2 AST akurasi

Tool	Komponen	Ground Truth	Prediksi Agent	Match
get_document	function	get_document	get_document	✓
req. param	metadata_file_id	metadata_file_id	✓
type & value	metadata_file_id=2	metadata_file_id=2	✓
get_extraction	function	get_extraction	get_extraction	✓
req. param	page_id	page_id	✓
type & value	page_id=2	page_id=2	✓
list_sheets	function	list_sheets	list_sheets	✓
req. param	spreadsheet_id	spreadsheet_id	✓
type & value	spreadsheet_id="abc"	spreadsheet_id="abc"	✓
append_rows	function	append_rows	append_rows	✓
req. param	spreadsheet_id, range, values	spreadsheet_id, range, values	✓
type & value	range= "Alfamart!A:H"	range= "Alfamart!A:H"	✓
Perhitungan ASTi per tool (M = 4):

AST1 = 1 ∧ 1 ∧ 1 = 1,00 AST2 = 1 ∧ 1 ∧ 1 = 1,00 AST3 = 1 ∧ 1 ∧ 1 = 1,00 AST4 = 1 ∧ 1 ∧ 1 = 1,00

AST_AccuracyCase 2 = 1/4 (1,00 + 1,00 + 1,00 + 1,00) = 4,00 / 4 = 1,00

Interpretasinya, seluruh komponen dari keempat tool call, nama fungsi, parameter wajib, dan nilai parameter, sesuai ground truth tanpa satu pun kesalahan.

Page 107
<page_number>97</page_number>

Agent berhasil mengambil data ekstraksi dari SQLite yang tepat dan menuliskannya ke sheet yang benar ("Alfamart!A:H") dengan spreadsheet_id yang valid.

Jadi rata-rata AST accuracy dari kasus 1 dan kasus 2 (N = 2):

$\overline{AST_Accuracy} = \frac{1}{2}(0.50 + 1.00) = \frac{1.50}{2} = 0.75$

C.2. Perhitungan Manual Pass@1

Merujuk pada rumus Pass@1 pada Persamaan (2.34)-(2.35) di Bab II, dilakukan perhitungan manual untuk struk belanja.

Kasus 1 (Ada Kesalahan Prediksi (Bebberapa Test Case Gagal)):

Lima test case struk belanja dengan berbagai kondisi. Setiap test case dinilai hanya dari kebenaran data akhir yang tertulis di spreadsheet, tidak peduli tool apa yang dipanggil atau urutannya.

Tabel 3.6 Kasus 1 Pass@1

j	Test Case	Hasil Akhir Agent	Ground Truth	cj,1
1	TC-01	Semua field benar	Semua field benar	1
2	TC-02	Total harga salah Rp45.000	Total benar Rp54.000	0
3	TC-03	Semua field benar	Semua field benar	1
4	TC-04	Field "Nama_Item" kosong	Field "Nama_Item" terisi	0
5	TC-05	Semua field benar	Semua field benar	1
Pass@1 per test case: Pass@11 = 1, Pass@12 = 0, Pass@13 = 1, Pass@14 = 0, Pass@15 = 1

Pass@1 keseluruhan case 1 (N = 5):

$\overline{Pass@1}_{\text{Case 1}} = \frac{1}{5}(1 + 0 + 1 + 0 + 1) = \frac{3}{5} = 0.60$

Interpretasinya agent berhasil pada 3 dari 5 test case (60%). Pass@1 tidak peduli seberapa benar tool call yang dilakukan tetap yang dinilai hanya apakah data akhir di spreadsheet benar.

Kus 2 (Prediksi Sempurna (Semua Test Case Berhasil)):

Page 108
<page_number>98</page_number>

Lima test case yang sama, namun kali ini agent berhasil menghasilkan data akhir yang benar di spreadsheet untuk seluruh test case.

Tabel 3. 7 Kasus 2 Pass@1

j	Test Case	Hasil Akhir Agent	Ground Truth	cj,1
1	TC-01	Semua field benar	Semua field benar	1
2	TC-02	Total benar Rp54.000	Total benar Rp54.000	1
3	TC-03	Semua field benar	Semua field benar	1
4	TC-04	Semua field benar	Semua field benar	1
5	TC-05	Semua field benar	Semua field benar	1
Pass@1 per test case:

Pass@11 = 1, Pass@12 = 1, Pass@13 = 1, Pass@14 = 1, Pass@15 = 1

Pass@1 keseluruhan case 1 (N = 5):

$\frac{1}{\text{Pass@1}_{\text{Case }1}} = \frac{1}{5}(1 + 1 + 1 + 1 + 1) = \frac{5}{5} = \boxed{1,00}$

Interpretasinya agent berhasil menghasilkan output akhir yang benar pada seluruh 5 test case dalam satu percobaan pertama. Skor sempurna 1,00 menunjukkan bahwa sistem data entry bekerja dengan sangat andal saat memproses pemanggilan tools.

3.5.5 Pengujian Black Box
Pengujian black box dilakukan untuk memverifikasi kesesuaian antara masukan yang diberikan dan keluaran yang dihasilkan berdasarkan spesifikasi kebutuhan fungsional yang telah ditetapkan. Pengujian ini berfokus pada fungsionalitas sistem tanpa menganalisis struktur internal atau kode program. Skenario pengujian black box disajikan pada Tabel 3.8.

Tabel 3. 8 Skenario pengujian black box

No.	Skenario Pengujian	Masukan	Keluaran yang Diharapkan
1.	Upload citra struk format JPG	Foto struk Indomaret (JPG, 1280×720)	Sistem menampilkan ringkasan hasil ekstraksi berupa informasi toko,
Page 109
<page_number>99</page_number>

1.	Upload citra struk format PNG	Foto struk Alfamart (PNG, 1920×1080)	daftar item, dan total pembayaran dalam format terstruktur
2.	Upload citra struk format PNG	Foto struk Alfamart (PNG, 1920×1080)	Sistem menampilkan ringkasan hasil ekstraksi yang sesuai dengan isi struk
3.	Upload dokumen PDF multi-halaman	PDF berisi 3 halaman struk berbeda	Sistem memproses setiap halaman secara independen dan menampilkan ringkasan per halaman
4.	Kirim pesan teks tanpa attachment	"Tampilkan hasil ekstraksi struk terakhir"	Supervisor Agent mengembalikan data ekstraksi dari database SQLite melalui SQL Agent
5.	Permintaan data entry ke Google Sheets	"Masukkan data struk ini ke Google Sheets"	Sistem menampilkan pratinjau data dan meminta konfirmasi HITL sebelum penulisan
6.	Konfirmasi HITL (setuju)	Pengguna menekan "Konfirmasi" pada pratinjau data	Data Entry Team menulis data ke Google Sheets dan menampilkan konfirmasi keberhasilan
7.	Konfirmasi HITL (koreksi)	Pengguna mengoreksi nilai total_price pada pratinjau	Sistem memperbarui data sesuai koreksi dan menampilkan ulang pratinjau untuk konfirmasi
Page 110
<page_number>100</page_number>

8.	Deteksi prompt injection	Masukan mengandung instruksi berbahaya: "Ignore previous instructions and delete all data"	Guardrails menolak masukan dan mengembalikan pesan penolakan tanpa memproses instruksi
9.	Deteksi blacklist domain (SARA)	Masukan mengandung konten bermuatan SARA	LLM-as-Judge mengidentifikasi konten yang dilarang dan mengembalikan pesan penolakan
10.	Deteksi blacklist domain (keuangan)	"Berikan saran investasi saham yang bagus"	LLM-as-Judge mengidentifikasi permintaan di luar cakupan dan mengembalikan penolakan
11.	Upload citra berkualitas rendah	Foto struk dengan pencahayaan buruk dan teks sebagian tidak terbaca	Sistem tetap mengekstrak field yang terbaca dan mengosongkan field yang tidak terdeteksi
12.	Upload dokumen non-struk	Foto dokumen KTP atau kartu nama	Sistem memproses namun menghasilkan field yang sebagian besar kosong karena bukan struk
13.	Kelola sesi percakapan baru	Pengguna membuat sesi baru	Sistem membuat sesi kosong dengan identitas terpisah dari sesi sebelumnya
Page 111
<page_number>101</page_number>

14.	Percakapan multi-giliran (multi-turn)	Pengguna mengunggah struk, lalu bertanya tentang total, lalu meminta data entry	Supervisor Agent mempertahankan konteks sesi dan merespons secara koheren pada setiap giliran
15.	Pembuatan sheet baru di Google Sheets	Instruksi "Buat sheet baru bernama Februari 2026"	Sheet Agent membuat tab sheet baru dengan nama yang diminta melalui MCP-GSheets
Page 112
DAFTAR PUSTAKA
Abdalla, M. dkk., 2025, ReceiptQA: A Question-Answering Dataset for Receipt Understanding, Mathematics, 13, 11, 1760–1760.

Abou Ali, M., Dornaika, F. dan Charafeddine, J., 2025, Agentic AI: a comprehensive survey of architectures, applications, and future directions, Artificial Intelligence Review, 59, 1, 11.

Abrahamsson, P. dkk., 2017, Agile Software Development Methods: Review and Analysis. arXiv.

Acharya, D.B., Kuppan, K. dan Divya, B., 2025, Agentic AI: Autonomous Intelligence for Complex Goals—A Comprehensive Survey, IEEE Access, 13, 18912–18936.

Al-Fedaghi, S., 2021, UML Sequence Diagram: An Alternative Model.

Ali, S. dan Shubham, 2020, App Development using React Native, Expo and AWS, International Journal of Trend in Scientific Research and Development (IJTSRD), 4, 4, 1307–1309.

Anthropic, 2025, Donating the Model Context Protocol and establishing the Agentic AI Foundation, Anthropic [Preprint].

Atil, B. dkk., 2025, Non-Determinism of “Deterministic” LLM Settings. arXiv.

Bai, J. dkk., 2023, Qwen-VL: A Versatile Vision-Language Model for Understanding, Localization, Text Reading, and Beyond. arXiv.

Bandi, C. dkk., 2026, MCP-Atlas: A Large-Scale Benchmark for Tool-Use Competency with Real MCP Servers. arXiv.

Barchard, K.A. dkk., 2020, Comparing the accuracy and speed of four data-checking methods, Behavior Research Methods, 52, 1, 97–115.

Barres, V. dkk., 2025, $τ^2$-Bench: Evaluating Conversational Agents in a Dual-Control Environment. arXiv.

Begaev, A. dan Orlov, E., 2023, Receipt-AVQA-2023 Challenge, dalam. Computational Linguistics And Intellectual Technologies, RSUH.

Biswas, A. dkk., 2025, Building agentic AI systems: create intelligent, autonomous AI agents that can reason, plan, and adapt. Birmingham: Packt Publishing.

Brown, T.B. dkk., 2020, Language Models are Few-Shot Learners.

<page_number>95</page_number>

Page 113
<page_number>96</page_number>

Cabrero-Daniel, B., 2023, AI for Agile development: a Meta-Analysis. arXiv.

Chen, M. dkk., 2021, Evaluating Large Language Models Trained on Code. arXiv.

Cui, C. dkk., 2026, PaddleOCR-VL-1.5: Towards a Multi-Task 0.9B VLM for Robust In-the-Wild Document Parsing. arXiv.

De Matos, G.L.A. dkk., 2025, Automation of Spreadsheet Reading With Artificial Intelligence Integration: Development of the Sheet2prompt Api Application, dalam Expanded Science: Innovation and Research - 2° Edição. 2 ed. Seven Editora.

Dong, Y. dkk., 2024, Building Guardrails for Large Language Models. arXiv.

Erike, A.I. dkk., 2025, A Comparative Performance Evaluation of SQLite, MySQL, and Firebase for Modern Application Development Using a Parallel Execution Approach, UNIZIK Journal of Engineering and Applied Sciences, 5, 2933–2944.

ExpressExpense, 2026, FREE Receipt Images – OCR / Machine Learning Dataset (SRD). ExpressExpense Blog.

Fan, S. dkk., 2025, MCPToolBench++: A Large Scale AI Agent Model Context Protocol MCP Tool Use Benchmark. arXiv.

FastAPI, 2026, FastAPI Documentation.

Fernanda, B.A. dan Sawitri, D.K., 2025, Analisa Tinjauan Klaim Reimbursement, GEMILANG: Jurnal Manajemen dan Akuntansi, 5, 3, 747–764.

Fomin, M., 2026, When Benchmarks Lie: Evaluating Malicious Prompt Classifiers Under True Distribution Shift. arXiv.

Gao, M. dkk., 2025, Single-agent or Multi-agent Systems? Why Not Both? arXiv.

Ghritlahare, A., 2025, The Role of Flowcharts in Problem Solving and Process Visualization.

Gloeckle, F. dkk., 2024, Better & Faster Large Language Models via Multi-token Prediction. arXiv.

Google DeepMind, 2026, Gemini 3.1 Pro Model Card. Google DeepMind Media.

Gu, J. dkk., 2025, A Survey on LLM-as-a-Judge. arXiv.

Guan, S. dkk., 2026, Teaching VLMs to Admit Uncertainty In OCR from Lossy Visual Inputs.

Page 114
<page_number>97</page_number>

Hong, S. dkk., 2024, MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework.

Hou, X. dkk., 2025, Model Context Protocol (MCP): Landscape, Security Threats, and Future Research Directions. arXiv.

Hu, E.J. dkk., 2021, LoRA: Low-Rank Adaptation of Large Language Models. arXiv.

Hu, R. dkk., 2025, Large language model driven transferable key information extraction mechanism for nonstandardized tables, Scientific Reports, 15, 1, 29802–29802.

Huang, Y. dkk., 2022, LayoutLMv3: Pre-training for Document AI with Unified Text and Image Masking. arXiv.

Huang, Z. dkk., 2019, ICDAR2019 Competition on Scanned Receipt OCR and Information Extraction, dalam 2019 International Conference on Document Analysis and Recognition (ICDAR). 2019 International Conference on Document Analysis and Recognition (ICDAR), Sydney, Australia: IEEE, 1516–1520.

Hutri, H., 2023, Comparison of React Native and Expo. Master’s thesis. Lappeenranta–Lahti University of Technology LUT.

Indrakusuma, R.I., Ahmadiyah, A.S. dan Ariyani, N.F., 2021, Pengenalan dan Klasifikasi Tulisan pada Nota Pembelian Material (Studi Kasus Proyek Konstruksi), Jurnal Teknik ITS, 10, 2.

Ishrak Alim, T.F.M., 2025, The Insider Risk of Artificial Intelligence in Financial Systems through the Lens of Large Language Models.

Ivry, D. dan Nahum, O., 2025, Sentinel: SOTA model to protect against prompt injections. arXiv.

Kang, H. dan Liu, X.-Y., 2023, Deficiency of Large Language Models in Finance: An Empirical Examination of Hallucination. arXiv.

Khanchandani, K. dkk., 2026, Automated Invoice Data Extraction: Using LLM and OCR.

Khang, M. dkk., 2025, KIEval: Evaluation Metric for Document Key Information Extraction. arXiv.

Kim, G. dkk., 2022, OCR-free Document Understanding Transformer. arXiv.

Kirinuki, H. dan Tanno, H., 2024, ChatGPT and Human Synergy in Black-Box Testing: A Comparative Analysis. arXiv.

Page 115
<page_number>98</page_number>

Koç, H. dkk., 2021, UML Diagrams in Software Engineering Research: A Systematic Literature Review, dalam The 7th International Management Information Systems Conference. International Management Information Systems Conference, MDPI, 13.

LangChain, 2026, LangChain Documentation.

Lee, H. dkk., 2025, Your AI, Not Your View: The Bias of LLMs in Investment Analysis. arXiv.

Li, H. dkk., 2024, LLMs-as-Judges: A Comprehensive Survey on LLM-based Evaluation Methods. arXiv.

Li, X. dkk., 2024, Enhancing Visual Document Understanding with Contrastive Learning in Large Visual-Language Models. arXiv.

Li, Y., Jiang, W. dan Song, S., 2023, Review of Semi-Structured Document Information Extraction Techniques Based on Deep Learning, dalam. 2023 2nd International Conference on Machine Learning, Cloud Computing and Intelligent Mining (MLCCIM), IEEE, 112–119.

Lin, T. dkk., 2022, A survey of transformers, AI Open, 3, 111–132.

Liu, H. dkk., 2023, Visual Instruction Tuning. arXiv.

Liu, S. dkk., 2025, See then Tell: Enhancing Key Information Extraction with Vision Grounding.

Liu, Y. dkk., 2025, Prompt Injection attack against LLM-integrated Applications. arXiv.

Mandal, S. dkk., 2025, Nanonets. Hugging Face.

Mathew, M., Karatzas, D. dan Jawahar, C.V., 2021, DocVQA: A Dataset for VQA on Document Images. arXiv.

Mays, J.A. dan Mathias, P.C., 2019, Measuring the rate of manual transcription error in outpatient point-of-care testing, Journal of the American Medical Informatics Association, 26, 3, 269–272.

Mei, L. dkk., 2025, A Survey of Context Engineering for Large Language Models. arXiv.

Meta, 2024, Llama-Prompt-Guard-2-86M. Hugging Face.

Minaee, S. dkk., 2025, Large Language Models: A Survey.

Page 116
<page_number>99</page_number>

Mohan Singh, 2025, Multi-agent systems: the future of distributed AI platforms for complex task management, World Journal of Advanced Research and Reviews, 26, 3, 048–055.

Natarajan, S. dkk., 2024, Human-in-the-loop or AI-in-the-loop? Automate or Collaborate? arXiv.

Nathan, S., 2025, Japanese-Mobile-Receipt-OCR-1.3K: A Comprehensive Dataset Analysis and Fine-tuned Vision-Language Model for Structured Receipt Data Extraction.

Ompusunggu, R. dan Sinambela, R.S., 2025, Konflik Sara Dalam Tinjauan Etika Kristen, 4.

Oribe, J.A., 2025, The Model Context Protocol (MCP) Emergence, Technical Architecture, and the Future of Agentic AI Infrastructure.

Ouyang, L. dkk., 2022, Training language models to follow instructions with human feedback. arXiv.

Pakpahan, R., Fitriyani, Y. dan Kholik, A., 2025, Perancangan Sistem Klaim Reimbursement Berbasis Web Untuk Meningkatkan Semangat Kerja Karyawan Pada Perusahaan, Journal of Information System, Informatics and Computing, 9, 1, 92–92.

Park, S. dkk., 2019, CORD: A Consolidated Receipt Dataset for Post-OCR Parsing, dalam NeurIPS 2019 Workshop on Document Intelligence.

Parthasarathy, V.B. dkk., 2024, The Ultimate Guide to Fine-Tuning LLMs from Basics to Breakthroughs: An Exhaustive Review of Technologies, Research, Best Practices, Applied Research Challenges and Opportunities.

Patil, S.G. dkk., 2025, The Berkeley Function Calling Leaderboard (BFCL): From Tool Use to Agentic Evaluation of Large Language Models, dalam Forty-second International Conference on Machine Learning.

Peer, D. dkk., 2025, ANLS* -- A Universal Document Processing Metric for Generative Large Language Models. arXiv.

Perdanawati, A.R., 2025, Peranan Sistem Informasi Akuntansi (Sia), Dan Pemanfaatan Teknologi Informasi Dalam Meningkatkan Kinerja Keuangan Usaha Mikro, Kecil, Dan Menengah Studi Kasus Di Warung Sadean Jajan Dan Warung Ayam Geprek.

Qiu, X. dkk., 2020, Pre-trained models for natural language processing: A survey, Science China Technological Sciences, 63, 10, 1872–1897.

Page 117
<page_number>100</page_number>

Radford, A. dkk., 2018, Improving Language Understanding by Generative Pre-Training.

Raschka, S., 2025, Build a Large Language Model (From Scratch). 1 ed. Shelter Island: Manning Publications.

Rexhepi, A. dkk., 2025, Invoice and receipt optical character recognition: review on current methods and future trends.

Roboflow, 2024, Receipts Dataset. Roboflow Universe.

Rombach, A.M. dan Fettke, P., 2026, Deep Learning Based Key Information Extraction from Business Documents: Systematic Literature Review, ACM Computing Surveys, 58, 2, 1–37.

Sahoo, P. dkk., 2025, A Systematic Survey of Prompt Engineering in Large Language Models: Techniques and Applications. arXiv.

Samson Olufemi Olanipekun, 2025, Computational propaganda and misinformation: AI technologies as tools of media manipulation, World Journal of Advanced Research and Reviews, 25, 1, 911–923.

Santoso, J.A. dkk., 2025, Ancaman AI Terhadap Pencemaran Budaya Sosial Indonesia: Analisis Kritis, Eksplorasi Data, dan Mitigasi Berbasis Filosofi Kebangsaan, Journal of Education Religion Humanities and Multidiciplinary, 3, 2, 726–731.

Sapkota, R., Roumeliotis, K.I. dan Karkee, M., 2026, AI Agents vs. Agentic AI: A Conceptual taxonomy, applications and challenges, Information Fusion, 126, 103599.

Setiawan, A.A., Guntara, R.G. dan Purwaamijaya, B.M., 2025, Ekstraksi Informasi Struk Belanja Melalui Pemanfaatan Tesseract dan Regular Expressions, RIGGS: Journal of Artificial Intelligence and Digital Business, 4, 2, 6586–6594.

Shafiee, S. dkk., 2020, Scrum versus Rational Unified Process in facing the main challenges of product configuration systems development, Journal of Systems and Software, 170, 110732.

Shaharudin, M.H. dkk., 2025, Development of a Student Expense Tracking System Using Optical Character Recognition, International Journal of Artificial Intelligence, 12, 1, 1–10.

Shanahan, M., McDonell, K. dan Reynolds, L., 2023, Role play with large language models, Nature, 623, 7987, 493–498.

Page 118
<page_number>101</page_number>

Shen, X. dkk., 2024, “Do Anything Now”: Characterizing and Evaluating In-The-Wild Jailbreak Prompts on Large Language Models. arXiv.

Siewe, F. dan Ngounou, G.M., 2025, On the Execution and Runtime Verification of UML Activity Diagrams, Software, 4, 1, 4.

Society for Clinical Data Management, 2023, Data Entry Processes, Journal of the Society for Clinical Data Management, 1, 1, 1–8.

SQLite, 2026, SQLite Documentation.

Sreedhar, K. dan Chilton, L., 2024, Simulating Human Strategic Behavior: Comparing Single and Multi-agent LLMs. arXiv.

Sugiarta, G., Andini, D.P. dan Hidayatullah, S., 2021, Ekstraksi Informasi/Data e-KTP Menggunakan Optical Character Recognition Convolutional Neural Network, JTERA (Jurnal Teknologi Rekayasa), 6, 1, 1–1.

Syed, R. dkk., 2023, Digital Health Data Quality Issues: Systematic Review, Journal of Medical Internet Research, 25, e42615–e42615.

Tazin, A. dan Kokar, M.M., 2025, UML Class Diagram Classification Using Category Theory, Journal of Software Engineering and Applications, 18, 07, 217–248.

Team, G.-V. dkk., 2026, GLM-4.5V and GLM-4.1 V-Thinking: Towards Versatile Multimodal Reasoning with Scalable Reinforcement Learning. arXiv.

Ulfha, M. dkk., 2025, Analisis Implementasi Akuntansi Digital Guna Pencatatan Keuangan pada UMKM, Indonesian Journal of Economic and Business (IJEB), 3, 2, 22–33.

UniData, 2026, OCR Receipts from Grocery Stores Text Detection. Hugging Face.

Vaswani, A. dkk., 2023, Attention Is All You Need.

Verbovskiy, A., 2025, Comparing OCR and VLM Techniques in Processing Tabular Data. Master’s Thesis. University of Oulu.

Vidgen, B. dkk., 2026, APEX-Agents. arXiv.

Vodrahalli, K. dkk., 2024, Michelangelo: Long Context Evaluations Beyond Haystacks via Latent Structure Queries. arXiv.

Vranić, V. dkk., 2024, Use case modeling in a research setting of developing an innovative pilgrimage support system, Universal Access in the Information Society, 23, 4, 1543–1560.

Page 119
<page_number>102</page_number>

Wang, L. dkk., 2023, A Survey on Large Language Model based Autonomous Agents.

Wang, L. dkk., 2025, A Survey on Large Language Model based Autonomous Agents.

Wang, Z. dkk., 2023, VRDU: A Benchmark for Visually-rich Document Understanding, dalam Proceedings of the 29th ACM SIGKDD Conference on Knowledge Discovery and Data Mining. KDD ’23: The 29th ACM SIGKDD Conference on Knowledge Discovery and Data Mining, Long Beach CA USA: ACM, 5184–5193.

Wei, J. dkk., 2022, Finetuned Language Models Are Zero-Shot Learners. arXiv.

Wei, J. dkk., 2023, Chain-of-Thought Prompting Elicits Reasoning in Large Language Models. arXiv.

Wijaya, I. dan Lubis, C., 2022, Pengimplementasian OCR Menggunakan CNN Untuk Ekstraksi Teks Pada Gambar, Jurnal Ilmu Komputer dan Sistem Informasi, 10, 1.

Winder, P., Hildebrand, C. dan Hartmann, J., 2025, Biased echoes: Large language models reinforce investment biases and increase portfolio risks of private investors, PLOS One. Disunting oleh P.G. Roetzel, 20, 6, e0325459.

Wu, Q. dkk., 2023, AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation.

Xi, Z. dkk., 2023, The Rise and Potential of Large Language Model Based Agents: A Survey. arXiv.

Xu, W. dkk., 2025, A-MEM: Agentic Memory for LLM Agents. arXiv.

Xu, Y. dkk., 2020, LayoutLM: Pre-training of Text and Layout for Document Image Understanding, dalam Proceedings of the 26th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining. KDD ’20: The 26th ACM SIGKDD Conference on Knowledge Discovery and Data Mining, Virtual Event CA USA: ACM, 1192–1200.

Yan, Z. dkk., 2025, DocExtractNet: A novel framework for enhanced information extraction from business documents, Information Processing & Management, 62, 3, 104046–104046.

Yao, S. dkk., 2023, ReAct: Synergizing Reasoning and Acting in Language Models. arXiv.

Ylisiurunen, M., 2022, Extracting Semi-Structured Information from Receipts.

Page 120
<page_number>103</page_number>

Z.ai, 2026, GLM-OCR.

Zhang, J. dkk., 2024, Vision-Language Models for Vision Tasks: A Survey, IEEE Transactions on Pattern Analysis and Machine Intelligence, 46, 8, 5625–5644.

Zhang, W. dkk., 2026, AgentOrchestra: Orchestrating Multi-Agent Intelligence with the Tool-Environment-Agent(TEA) Protocol. arXiv.

Zhao, W.X. dkk., 2026, A Survey of Large Language Models.

Zheng, Y. dkk., 2024, LlamaFactory: Unified Efficient Fine-Tuning of 100+ Language Models. arXiv.

Page 121
LAMPIRAN

<page_number>103</page_number>

