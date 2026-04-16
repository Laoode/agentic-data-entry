## Contents
- Keywords:
- 1 Introduction
- 2 Related Works
  - 2.1 Document KIE Methdology
  - 2.2 Existing Metrics
- 3 Problem Definition
  - 3.1 Document KIE Task
  - 3.2 Measuring Document KIE Model in Industrial Settings
- 4 KIEval
  - 4.1 Structured Evaluation – Entity and Group Level
  - 4.2 Aligned Metric Formulation
- 5 Experiment Settings
  - 5.1 Datasets
  - 5.2 Document KIE Models
  - 5.3 Grouping Information
  - 5.4 Experiment Details
- 6 Results and Discussion
  - 6.1 Structured Evaluation
  - 6.2 Metrics from the Correction Cost Perspective
- 7 KIE Evaluation for RPA System
- 8 Conclusion
- References
- Appendix 0.A Datasets
- Appendix 0.B Multimodal LLM prompt for CORD KIE
- Appendix 0.C Automation Trade-off Analysis Metric

## Abstract

Abstract Document Key Information Extraction (KIE) is a technology that transforms valuable information in document images into structured data, and it has become an essential function in industrial settings.
However, current evaluation metrics of this technology do not accurately reflect the critical attributes of its industrial applications.
In this paper, we present KIEval, a novel application-centric evaluation metric for Document KIE models.
Unlike prior metrics, KIEval assesses Document KIE models not just on the extraction of individual information (entity) but also of the structured information (grouping).
Evaluation of structured information provides assessment of Document KIE models that are more reflective of extracting grouped information from documents in industrial settings.
Designed with industrial application in mind, we believe that KIEval can become a standard evaluation metric for developing or applying Document KIE models in practice.
The code will be publicly available.

###### Keywords:

## 1 Introduction

Figure: Figure 1: Example of CORD dataset (receipts). The dataset has non-grouped and grouped entities (non-grouped entities form a special group), and requires structured predictions including Menu groups: Menu.name and Menu.price. Errors in model predictions are not limited to individual key-value pair errors but also in the extraction of structural relation between entities (marked in red). Both error types must be considered in Document KIE model evaluation.
Refer to caption: x1.png

Document Key Information Extraction (KIE) is a well-known task of converting information from document images into structured data and has gained much attention from both the academia and industry over the years  [24, 23, 9, 5, 8, 12, 17, 13, 10]. One common application of Document KIE in industrial settings lies in Robotic Process Automation (RPA) of document digitisation which aims to extract, structure, and store the data in document images into databases for various downstream applications. Information extracted from documents is often presented as key-value pairs (e.g. Menu.name: “AMERICANO”) that are frequently interrelated (e.g. Menu.name & Menu.price), forming the basis of structured information in documents.

Despite such application settings, a standardized evaluation metric for Document KIE models has yet to be established and existing metrics used in prior works fail to consider several key components from the application’s standpoint. The main causes of disparity between the existing evaluation metrics and application settings can be attributed to: neglecting structured nature of information in assessment and insufficient alignment of metric formulation with the industrial applications. Detailed explanations of these causes are as follows (corresponding visualisations are shown in Fig. [1](https://arxiv.org/html/2503.05488v2#S1.F1) and [2](https://arxiv.org/html/2503.05488v2#S1.F2)):

Structured nature in information refers to the presence of structural relation between key-value pairs in documents. Referring to the example in Fig. [1](https://arxiv.org/html/2503.05488v2#S1.F1) and [2](https://arxiv.org/html/2503.05488v2#S1.F2), each values of the entity-type, Menu.name, has contextual linkage to different values of Menu.price. Existing metrics, however, mainly focus on the assessment of individual entity extraction, while reflecting limited or no evaluation for extraction of such structured information. In industrial applications, however, the lack of such structured information can lead to critical information loss when storing data in relational databases for downstream tasks.

Insufficient alignment of existing metrics’ design refers to gaps arising due to the formulations that are not fully representative of Document KIE applications in industrial settings. Existing metrics, such as the Entity-level F1 metric, often distinguishes KIE model’s erroneous prediction (False-Positive, FP) from missed prediction (False-Negative, FN) in metric formulations. Such distinction, while well-suited for model development, precipitates clear disparity with application settings where KIE errors are often perceived in number of correction counts needed. It is worth noting that, correction count refers to number of value editing (one of substitution, addition, or deletion) steps needed to convert KIE predictions to ground-truth values.

Figure: Figure 2: Comparison of evaluation metrics for KIE tasks. Note that the ground-truth and predictions follow the same Document Image in Fig. [1](https://arxiv.org/html/2503.05488v2#S1.F1). The red boxes indicate the errors accounted for by the respective metrics during evaluation. Entity-level F1 does not account for structural relations unlike the proposed KIEval metric which performs both Entity-level and Group-level evaluations based on the group-matching information (blue links).
Refer to caption: x2.png

To address the causes of disparity identified above, we propose an evaluation metric with application-centric design named: KIEval (Key Information Extraction evaluation). Firstly, KIEval is formulated to provide KIE model assessment in two different levels: entity-level (individual entities such as Menu.name) and group-level (sets of related entities such as Menu.name, Menu.price). In both levels of evaluation, prediction and ground-truth values are matched by conditioning on information structure (group), facilitating structured-information level assessment of KIE models. Secondly, KIEval formulates KIE errors in terms of the number of substitution, addition, or deletion steps needed. Such formulation, instead of the conventional FP and FN, aims to better represent the eventual cost which KIE errors incur in application settings.

In this work, our key contributions can be summarized as follows. 1) We propose KIEval (Key Information Extraction evaluation) metric for Document KIE which incorporates structured information assessment in both entity and group-level evaluation. 2) Provision of KIE model evaluation in terms of information correction cost, bridging the disparity of existing metrics with industrial applications. 3) We also showcase a use-case study on how KIEval can be applied in RPA systems, highlighting its differences against existing metrics.

## 2 Related Works

### 2.1 Document KIE Methdology

Various types of approaches to Document KIE have been proposed over the years. One of the notable earlier works, LayoutLM [24], was the first to propose a multi-modal framework, incorporating both text and layout modalities in key information extraction from documents. The framework’s robust performance with simplistic design of BIO-tagging has motivated many follow-up works such as: BROS [8], LayoutLMv2 [23], LayoutLMv3 [9], and ERNIE-Layout [17]. Alternative forms of KIE with improved representational flexibility such as graph-based [10] and text generation [12, 13] frameworks were proposed in follow-up works to better capture dependencies between entities and effectively capture structured information from documents. With the rise of LLM applications, recent works, such as ICL-D3IE [6] and SAIL [27], have leveraged the flexibility of LLMs to tackle Document KIE in zero and few-shot settings.

### 2.2 Existing Metrics

Entity-level F1 score is one of the most commonly used metrics for Document KIE model evaluation. Upon extracting entity-wise key-value pairs, they are matched against the ground-truth key-value pairs, where the predicted pair is considered valid if an exact-match can be found in the ground-truth set. Such exact-match statistics are collated across different entities in the dataset to evaluate the model’s entity-level F1 score. Commonly used in prior works [24, 23, 9, 17], entity-level F1 score evaluates the degree to which model’s extracted information exactly matches the expected key-value content in the document.

This metric however, not only disregards structural relation between entities during entity-level F1 evaluation but also does not provide any assessment for group-level information extraction. In industrial applications, entities extracted often form meaningful information when grouped with other entities that are structurally related (i.e group), such as the grouping of Menu.name, Menu.quantity, and Menu.price, in receipts. Variations of entity-level F1 score were employed in prior works such as group-constrained entity-level F1 in SPADE  [10], Entity Extraction and Linking F1 in BROS [8], offering a more comprehensive assessment of KIE models. These variations of entity-level F1 metric underscores the necessity for a standardized metric for KIE model evaluation in the field of Document AI. Furthermore, the absence of direct assessment for group-level information extraction in these metrics highlights the disparity in meeting the industrial application requirements.

Tree Edit Distance (TED) score is another type of KIE evaluation metric, commonly adopted in text-generation based KIE models [12]. In contrary to the exact-match based entity-level F1 score, TED adopts a soft-match approach to avoid over-penalisation of model’s KIE. Edit distance based metric could provide a more objective assessment of the model by mitigating the impact of minor discrepancies, such as those between “ice cream” and “ice-cream”, which could lead to underestimation of model’s KIE performance. As discussed in Donut [12], TED metric can be applied to KIE models by first representing the prediction and ground truth as trees, before evaluating the edit distance between them. With the structural relation between entities captured using tree representation, this metric offers assessment of not only the model’s entity-level KIE performance but also at the group-level.

Despite such capacity of TED metric, its soft-match approach could exacerbate the discrepancy when applied to industrial settings. Taking automatic KIE setting as an example, pairs of information with minor edit distance could refer to completely different items such as “Pear” and “Pea” or “7000” and “1000”. Consequently, it is required of evaluation metrics to be stringent and provision of partial scores (with edit distance) could offer a misleading KIE assessment.

Other notable metrics include Average Normalized Levenshtein Similarity (ANLS) [2, 19] and hybrid metric of exact-match and edit distance [26]. ANLS aims to reduce the effect of overestimation of KIE models by constraining the maximum edit-distance between prediction and ground-truth to a pre-specified threshold value (e.g. 0.5) beyond which, no partial score is given. Hybrid metric, on the other hand, is a weighted arithmetic mean of the KIE model’s entity-level F1 and inverse Normalized Edit Distance (NED). Nevertheless, these metrics still share the limitations of Entity-level F1 and TED metrics, and do not provide group-level assessment of KIE models.

## 3 Problem Definition

### 3.1 Document KIE Task

Document KIE is a task in the field of Document Understanding (DU), with the objective of extracting structured key-value pairs from Document images. Commonly positioned as the task preceding various knowledge-application operations (e.g. financial data analysis), Document KIE is often faced with two principal challenges: (1) accurate extraction of key-value information, requiring value extraction and entity-key classification with minimal error, and (2) the discernment of structural relations between different key-value pairs, which demands accurate identification of contextual links between key-value pairs, to form a coherent group-level information unit.

### 3.2 Measuring Document KIE Model in Industrial Settings

To create an application-centric evaluation metric, following principal challenges of prior metrics must to be addressed: (1) absence of structural relation in metrics and (2) insufficient alignment of metric formulation with application settings.

Structural relation refers to the contextual linkage between key-value pairs associated with entities in documents. Entity key-value pairs that share contextual linkage are formally defined as a group, such as Menu.name and Menu.price in the CORD example (Fig. [1](https://arxiv.org/html/2503.05488v2#S1.F1)). Such structural relations present in documents need to be considered in both entity-level and group-level evaluations. Prior metrics in entity-level evaluation (e.g. Entity-level F1) show limited or no inclusion of structural relation, by evaluating each extracted key-value independent from the remaining key-value pairs. Prediction results visualized in Fig. [2](https://arxiv.org/html/2503.05488v2#S1.F2) clearly demonstrates this where, the prediction of {Menu.price: “54,545”} is not matched with the corresponding {Menu.name: “LIPTON PITCHER”}. Despite predicting a valid Menu.price key-value pair, this prediction is regarded erroneous due to failure in capturing the relation with contextually linked Menu.name key-value pair. This can be intuitively understood as: Menu.price key-value standalone does not provide meaningful information from the application point-of-view, unless paired with the corresponding Menu.name. In group-level evaluations, a more direct assessment of structural relation is conducted where, each group (instead of key-value pair) is treated as a unit of information extracted. Group-level evaluation provides essential assessment of the KIE model especially in industrial applications where information applications are often conducted in contextually related groups (e.g. Menu.name, Menu.price).

Fig. 3: F1 Score Examples in Three Different Scenarios
(a) Scenario #1 — Missing Information (FN)
| Ground-truth | Prediction |
|---|---|
| Menu.name | Menu.name |
| Americano ✅ | Americano ✅ |
| Latte **FN** | *(missing)* |

- **Recall** = (Americano) / (Americano + Latte) = **1/2**
- **Precision** = (Americano) / (Americano) = **1/1**
- **F1 = 2/3**

---

(b) Scenario #2 — Wrong Information (FN + FP)
| Ground-truth | Prediction |
|---|---|
| Menu.name | Menu.name |
| Americano ✅ | Americano ✅ |
| Latte **FN** | Juice **FP** |

- **Recall** = (Americano) / (Americano + Latte) = **1/2**
- **Precision** = (Americano) / (Americano + Juice) = **1/2**
- **F1 = 1/2**

---

(c) Scenario #3 — Unexpected Information (FP)
| Ground-truth | Prediction |
|---|---|
| Menu.name | Menu.name |
| Americano ✅ | Americano ✅ |
| *(none)* | Juice **FP** |

- **Recall** = (Americano) / (Americano) = **1/1**
- **Precision** = (Americano) / (Americano + Juice) = **1/2**
- **F1 = 2/3**

---

**Fig. 3:** F1 score examples in three different scenarios. From the application perspective,
the three different scenarios require the same number of error corrections:
- **(#1)** filling missing information
- **(#2)** replacing wrong information
- **(#3)** deleting the unexpected information
However, in the view of F1 scores, false negative (FN) and false positive (FP) are
separately counted to identify a representative score value, **F1**.

In addition to structural relation between key-value pairs, metric formulation is another factor that creates the disparity between the (prior works’) model-centric and (KIEval’s) application-centric design. Model-centric metric formulations often distinguish model’s erroneous prediction (FP) from missed prediction (FN), such as in Entity-level F1 metric. In industrial applications, however, it is more relevant to assess KIE models in terms of additional cost incurred due to KIE errors. To elaborate, with reference to Fig. [3(a)](https://arxiv.org/html/2503.05488v2#S3.F3.sf1), Entity-level F1 evaluation across the three scenarios implies lower KIE performance in scenario 2. From the application perspective, however, all of the three scenarios’ predictions incur the same cost of one editing operation (addition, substitution, or deletion) in KIE automation. Consequently, it is imperative to develop an application-centric metric formulation that accurately reflects the actual application settings.

Based on the key challenges of application-centric design defined above, our work’s proposed metric, KIEval, is designed with these factors in mind to bridge the disparity between the current metrics and industrial applications.

## 4 KIEval

### 4.1 Structured Evaluation – Entity and Group Level

In KIEval, to integrate structural relation into the KIE evaluation, group-matching was conducted between the predicted and ground-truth key-value pairs prior to entity-level and group-level evaluations. While variant of group-matching for entity-level evaluation was employed in [10], the lack of formal definition underscores its significance in the view of KIE metric standardisation.
To illustrate, let $\mathbf{PR}=\{{\text{pr}}_{1},{\text{pr}}_{2},...,{\text{pr}}_{N}\}$ be a set of predicted groups and $\mathbf{GT}=\{\text{gt}_{1},\text{gt}_{2},...,{\text{gt}}_{M}\}$ be ground-truth groups, where each group consists of a set of entities represented by tuples, (entity-type, value). The non-group entities (i.e. company.name and company.number in receipt) are included in $1$-st group to represent all entities with the same structural format. For the formal definition of group-matching, we define a matching score $S_{(n,m)\textbf{}}$ counting the identical entities between ${\text{pr}}_{n}$ and ${\text{gt}}_{m}$. Based on the matching scores between groups, each prediction group is matched with a ground-truth group through Hungarian matching to obtain a group-matched set of groups, $\mathbf{G}=\{(n_{1},m_{1}),(n_{2},m_{2}),...,\}$, where $n_{g}$ and $m_{g}$ indicate the $g$-th matched indices of predicted and ground-truth groups, respectively, and $|\mathbf{G}|$ results as $\min(N,M)$. The group-matching can be defined as follows:

$$ $\mathbf{G}=\text{Hungarian}(\mathbf{PR},\mathbf{GT},\mathbf{S})$ (1) $$

where $\mathbf{S}$ indicates a set of matching scores, $S_{(n,m)}$, between all pairs between predictions and ground-truth. For an entity $e$ at a matching $(n,m)$, F1 statistics such as True-Positive (TP), False-Negative (FN), and False-Positive (FP) can be calculated as follows;

$$ ${TP}_{(n,m)}^{e}=S_{(n,m)}^{e},{FN}_{(n,m)}^{e}=\text{N}_{e}({\text{gt}}_{m})- S_{(n,m)}^{e},{FP}_{(n,m)}^{e}=\text{N}_{e}({\text{pr}}_{n})-S_{(n,m)}^{e}$ (2) $$

where $S_{(n,m)}^{e}$ indicates the number of identical entity pairs, which has entity-type $e$ between $n$-th predicted and $m$-th ground-truth groups. The $\text{N}_{e}(\cdot)$ represents the operation counting entity-type $e$ in a group. In other words, ${TP}_{(n,m)}^{e}$ indicates the matched entity, and ${FN}_{(n,m)}^{e}$ and ${FP}_{(n,m)}^{e}$ represent the remaining ground-truths and predictions in the specific match $(n,m)$ in terms of entity type $e$, respectively. To calculate a final cumulated score, KIEval Entity F1, the total F1 statistics are identified as follows:

$$ $\displaystyle{TP}^{\text{entity}}$ $\displaystyle=\sum_{(n,m)\in\mathbf{G}}\sum_{e}{TP}_{(n,m)}^{e}$ (3) $\displaystyle{FN}^{\text{entity}}$ $\displaystyle=\sum_{m}^{M}\sum_{e}\text{N}_{e}({\text{gt}}_{m})-TP^{\text{ entity}}$ (4) $\displaystyle{FP}^{\text{entity}}$ $\displaystyle=\sum_{n}^{N}\sum_{e}\text{N}_{e}({\text{pr}}_{n})-TP^{\text{ entity}}$ (5) $$

The statistics can be used to calculate KIEval Entity F1 metric using standard precision and recall manners.

Group-level evaluation, KIEval Group F1, is also conducted on the group-matched $\mathbf{G}$ where F1 statistics are evaluated across different groups. Unlike KIEval Entity F1 which treats all entities in a group as a unit of information to evaluate F1 statistics, KIEval Group F1 evaluates on the entire group as a unit of information. It should be noted that, group-level evaluation is conducted on all but the first element of $\mathbf{G}$ (i.e. $\mathbf{G}^{\prime}$) as the first element represent non-group entities.

$$ $\mathbf{G}^{\prime}=\mathbf{G}\setminus{(n_{1},m_{1})}$ (6) $$

$$ ${TP}^{\text{group}}=\sum_{(n,m)\in\mathbf{G}^{\prime}}\mathbbm{1}[S_{(n,m)}^{e }=\text{N}_{e}({\text{gt}}_{m})=\text{N}_{e}({\text{pr}}_{n})\;\;\;\forall e]$ (7) $$

Eq. [7](https://arxiv.org/html/2503.05488v2#S4.E7) shows formulation of group-level True-Positive measure where counting identical pairs of prediction and ground truth groups in $\mathbf{G}^{\prime}$. In the equation, $\mathbbm{1}[\cdot]$ indicates a binary operator providing 1 when the predicted and ground-truth groups are identical. FN and FP are calculated by counting the remaining ground-truth and predicted groups, respectively. Finally, KIEval Group F1 can be identified with the same precision and recall fashion. Based on the formal definition of KIEval Entity F1 and KIEval Group F1 above, both formulations aim to incorporate structure relation assessment in evaluation at the entity and group-level, respectively.

### 4.2 Aligned Metric Formulation

While distinction of model’s erroneous prediction and missed prediction as FP and FN in metric formulation could be well-suited from the model-centric point-of-view, its misalignment in the standpoint of industrial application has motivated the formulation of our metric. KIEval’s application-centric design addresses this misalignment by conceptualizing KIE errors as correction costs incurred in application settings. Correction refers to one of the three editing steps: substitution, addition, and deletion of prediction values to match the ground-truth. For an entity $e$ at the matching condition $(n,m)\in\mathbf{G}$, the steps can be defined in terms of FN and FP as follows:

$$ $\displaystyle\text{Subs}_{(n,m)}^{e}$ $\displaystyle=\min(FP_{(n,m)}^{e},FN_{(n,m)}^{e})$ (8) $\displaystyle\text{Add}_{(n,m)}^{e}$ $\displaystyle=FN_{(n,m)}^{e}-\text{Subs}_{(n,m)}^{e}$ (9) $\displaystyle\text{Del}_{(n,m)}^{e}$ $\displaystyle=FP_{(n,m)}^{e}-\text{Subs}_{(n,m)}^{e}$ (10) $$

As can be seen, the substitution is defined as the minimum number of $FP_{(n,m)}^{e}$ and $FN_{(n,m)}^{e}$, which indicates the number of predictions that require modifications to match corresponding ground-truth values. The addition and deletion are the number of remaining $FN_{(n,m)}^{e}$ and $FP_{(n,m)}^{e}$, respectively. The number of error, $\text{Error}_{(n,m)}^{e}=\text{Subs}_{(n,m)}^{e}+\text{Add}_{(n,m)}^{e}+\text{
Del}_{(n,m)}^{e}$, is represented by summing the three error corrections. The total number of error can be defined as follows;

$$ $\text{Error}=\sum_{(n,m)\in\mathbf{G}}\sum_{e}\text{Error}_{(n,m)}^{e}+ \underbrace{\sum_{(*,m)\notin\mathbf{G}}\sum_{e}\text{N}_{e}({\text{gt}}_{m})} _{\text{Add unmatched gt}}+\underbrace{\sum_{(n,*)\notin\mathbf{G}}\sum_{e} \text{N}_{e}({\text{pr}}_{n})}_{\text{Del unmatched pr}}$ (11) $$

Here, the first term on the right-hand side indicates the number of error corrections in the group match condition $\mathbf{G}$, and the second and third terms represent the number of additions and deletions, respectively, for the non-matched groups. Finally, $\text{KIEval}_{\text{Aligned}}$ is calculated with the Error and the number of correct values, $TP$. The following equation shows the formulation;

$$ $\text{KIEval}_{\text{Aligned}}=\frac{TP^{\text{entity}}}{TP^{\text{entity}}+ \text{Error}}$ (12) $$

The $\text{KIEval}_{\text{Aligned}}$ not only better aligns with industrial applications, but also benefits from high interpretability due to its formulations in terms of well-known F1 components: TP, FP, and FN.

## 5 Experiment Settings

### 5.1 Datasets

Experiments were conducted with the KIEval metric on models trained using three widely used benchmark datasets in the Document KIE task, namely: SROIE, CORD and FUNSD, shown in Fig [4](https://arxiv.org/html/2503.05488v2#S5.F4).

Figure: Figure 4: Sample images from the SROIE (left), CORD (center), and FUNSD (right) datasets.
Refer to caption: x6.png

SROIE dataset refers to the dataset introduced in task 3 of Scanned receipts OCR and information extraction challenge of ICDAR 2019(^1^11https://rrc.cvc.uab.es/?ch=13). This dataset comprises of 626 train and 347 test receipt images, requiring participants’ models to extract key-value pairs of 4 entities: Company, Date, Address and Total price from these images.

Consolidated Receipt Dataset (CORD) [16] comprises of receipt images from shops and restaurants designed for the task of extracting grouped entities. Dataset’s annotation consists of 30 entities, which are categorized into 4 groups: Menu, Void menu, Subtotal, and Total. Entities within each group are contextually linked such as: Menu.name, Menu.price and Menu.quantity. There are 800 training, 100 validation and 100 testing images.

Form Understanding in Noisy Scanned Documents (FUNSD) [11] consists of 149 training and 50 test documents, which are noisy, scanned, and have various layouts. This dataset is composed of three entities: Header, Question, and Answer. FUNSD, unlike aforementioned datasets, allows each entity to hold multiple values within the same document image. To maintain consistency with prior works on FUNSD, all entities are regarded as non-group in our experiments.

### 5.2 Document KIE Models

Current works on Document KIE can be largely categories into two frameworks: sequence labeling and generative frameworks.

Prior works in the sequence labeling framework adopt tagging-based approach to extract key-value pairs from document images. In detail, with reference to CORD sample image in Fig. [4](https://arxiv.org/html/2503.05488v2#S5.F4), OCR is first applied to extract texts such as “Vt Pep Mocha” before tokenizing it into “Vt”, “Pep” and “Mocha”. The KIE model then processes these tokens, often conditioned with layout and image information, to provide token-wise label (e.g. BIO tag) classifications such as “B-Menu.name”, “I-Menu.name”, and “I-Menu.name” to the example text respectively. Tokenized texts along with their corresponding token-level tags are then postprocessed to form the final key-value pairs (e.g. Menu.name: “Vt Pep Mocha”). Representative works in this framework include: LayoutLM family [24, 23, 25, 9], StructuralLM [14], BROS [8], LiLT [21], and DocFormer [1].

Generative framework based models conduct KIE from document images by directly generating the key-value pairs as text. Taking the same CORD example in Fig. [4](https://arxiv.org/html/2503.05488v2#S5.F4), generative KIE models generates text sequence of key-value pairs such as: {Menu.name: “Vt Pep Mocha”, Menu.price: “4.95”}. OCR information can also be provided as auxiliary input to these KIE models. Notable generation methods include TILT [18], Donut [12], and Pix2Struct [13], where ResNet [7] or ViT [4] is commonly used for image encoder and Transformer decoder [20] for text decoder.

In this work, we conduct experiments using LayoutXLM [25] and LayoutLMv3 [9] models for the sequence labeling framework, and the Donut [12] model for the generative framework. Given recent advancements in large language model (LLM) applications for document intelligence, we also conduct zero-shot LLM-based KIE experiments with GPT-4o [15], Qwen2-VL [22] and InternVL 2.5 [3]. These experiments demonstrate how KIEval can provide additional insights into LLM evaluation within the KIE context.

### 5.3 Grouping Information

With prior KIE models mainly designed for KIE at the entity-level, we adopt simple methodology to extract grouping information prior to KIEval evaluations.

For models of sequence labeling framework, a simple slot filling method is adopted for grouping. To elaborate, given the set of entity-types constituting a group (e.g. Menu.name, Menu.price, … in CORD’s Menu group), KIE model’s output of these entity-types are sequentially filled in a slot filling manner to form groups. While different approaches for grouping extraction can be adopted, such as relation extraction [25] or graph-based method [10] on top of the KIE models, for the purpose of assessing the effectiveness of KIEval metric, a simple grouping method was employed. For text-generation based models, group-level information can be extracted by simple structuring of the target key-value pair text sequence such as JSON format strings.

### 5.4 Experiment Details

All sequence labeling and generation models were trained for 1,000 steps with a batch size of 16.
The initial learning rate was set to 5e-5, along with linear learning rate decay.
We used the provided OCR annotations along with images for experiments involving LayoutXLM [25] and LayoutLMv3 [9] while only the document image was provided for Donut [12] experiments. For reproducibility, all experiments were conducted using the models and datasets uploaded to Hugging Face Models and Datasets(^2^22https://huggingface.co).
Details can be found in Appendix A.
For multimodal LLMs, all experiments were conducted in zero-shot setting, and the prompts used can be found in Appendix B.

## 6 Results and Discussion

### 6.1 Structured Evaluation

Figure: Figure 5: Examples illustrating the difference between Entity F1 and KIEval. The above scenario is constructed to showcase metric disparities, whereas the scenario below is based on real prediction result from the Donut model.
Refer to caption: x7.png

The conventional Entity F1 metric fails to accurately represent the KIE model’s performance due to absence of structural relation consideration. Fig. [5](https://arxiv.org/html/2503.05488v2#S6.F5)(top) illustrates conceptual examples with corresponding metric scores across Entity F1, KIEval Entity F1 and KIEval Group F1. In Fig. [5](https://arxiv.org/html/2503.05488v2#S6.F5)(top), while both Prediction 1 and 2 display accurate entity-level key-value pair extractions, contextual relations (grouping) between different key-value pairs are not well-captured in Prediction 2. Such observations are not well-reflected in the conventional Entity F1 metric, scoring 1.0 across both predictions.

In industrial applications where both the key-value and contextual linkage information need to be extracted (if present), Entity F1’s insensitivity towards the latter could lead to sub-optimal reflection of the KIE model’s performance especially in RPA applications. KIEval Entity F1 and KIEval Group F1, on the contrary, provide distinct evaluations across the two predictions by taking into account of structural relations in the formulations. In KIEval Entity F1, despite error-free extraction of key-value pairs for each entity-type, Prediction 2 is penalized for its grouping errors, resulting in a score of $1/3$. Similarly in KIEval Group F1, where each group is treated as a single-unit of information instead of key-value pairs, Prediction 2 is evaluated to be completely incorrect, which is not discernible from the Entity F1 metric.

Fig. [5](https://arxiv.org/html/2503.05488v2#S6.F5)(bottom) depicts a sampled inference result of the Donut (generation KIE) model. Despite accurate extraction of Menu.name key-values, contextual linkage with other entity types are misaligned possibly due to tilt rotation of the receipt image. The conventional Entity F1 score of Menu.price entity does not reflect this error and assigns a full score of 1.0 unlike KIEval Entity F1 which penalizes the prediction accordingly.

**Table 1: Comparision of Entity F1, nTED, and KIEval. When group entities are absent, Entity F1 and KIEval Entity F1 yield identical values. Note: Donut displays substantially lower performance than other models due to its sole reliance on image input, unlike other models’ use of ground-truth OCR annotations.**
|  | LayoutXLM | LayoutLMv3 | Donut |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SROIE | CORD | FUNSD | SROIE | CORD | FUNSD | SROIE | CORD |  |
| Entity F1 | 91.77 | 95.43 | 84.02 | 91.87 | 95.13 | 85.87 | 83.85 | 84.93 |
| nTED | 97.24 | 94.86 | 61.96 | 96.91 | 94.43 | 69.36 | 96.17 | 90.62 |
| KIEval Entity F1 | 91.77 | 92.88 | 84.02 | 91.87 | 91.84 | 85.87 | 83.85 | 84.47 |
| KIEval Group F1 | - | 82.68 | - | - | 82.11 | - | - | 68.26 |
| KIEval${}_{\text{Aligned}}$ | 90.32 | 89.02 | 79.22 | 91.15 | 88.15 | 80.22 | 83.57 | 79.70 |

Evaluation results for different metrics across all models and datasets are shown in Table [1](https://arxiv.org/html/2503.05488v2#S6.T1). For nTED, its soft-match approach inaccurately compares KIE performance, as seen in LayoutXLM and LayoutLMv3 on SROIE, where trends differ from Entity F1 and KIEval Entity F1. For Entity F1, the differences compared to KIEval Entity F1 are prominent in CORD dataset where contextual links (grouping) between entities are present. KIEval Entity F1 consistently underperforms compared to Entity F1 in CORD across all models, despite achieving equivalent scores in SROIE and FUNSD. This discrepancy highlights the overestimation of KIE model performance when structural relations are ignored, while the metric converges to Entity F1 in datasets without grouping.

**Table 2: Comparison of Entity F1 and KIEval Entity F1 across generative models including multimodal LLMs on the CORD dataset. All multimodal LLMs are evaluated in a zero-shot setting. The difference between Entity F1 and KIEval Entity F1 serves to highlight information structure awareness of LLMs in KIE.**
|  | Donut | GPT-4o | Qwen2-VL | InternVL 2.5 |
| --- | --- | --- | --- | --- |
| Entity F1 | 84.93 | 73.56 | 77.07 | 54.99 |
| KIEval Entity F1 | 84.47 | 72.93 | 77.07 | 54.54 |
| Difference | 0.46 | 0.63 | 0.00 | 0.45 |

Figure: Figure 6: Sample of CORD dataset, illustrating the performance gap between Entity F1 and KIEval Entity F1 in GPT-4o, highlighting the importance of structure awareness evaluation on top of the existing KIE metric.
Refer to caption: x8.png

The discrepancy is also evident in multimodal LLM evaluation, as shown in Table [2](https://arxiv.org/html/2503.05488v2#S6.T2). The difference between Entity F1 and KIEval Entity F1 provides deeper insight into the LLM’s ability in grouping correctly extracted information into the expected semantic structures. Based on the CORD results, Qwen2VL outperforms not only in extraction but also in grouping these information accurately. Fig. [6](https://arxiv.org/html/2503.05488v2#S6.F6) shows an example where GPT-4o correctly extracts key information but groups it into an incorrect structure, showcasing KIEval’s utility in offering a new perspective for assessing LLMs in KIE.

### 6.2 Metrics from the Correction Cost Perspective

**Table 3: Comparison of FP + FN and Correction (Subs + Add + Del) statistics. Both Add and Del indicate the sum of counts within the matched and unmatched groups. Note: Correction refers to the number of correction steps taken.**
|  | LayoutXLM | LayoutLMv3 | Donut |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SROIE | CORD | FUNSD | SROIE | CORD | FUNSD | SROIE | CORD |  |
| FP + FN | 231 | 190 | 637 | 226 | 218 | 566 | 447 | 404 |
| Subs | 93 | 37 | 198 | 102 | 53 | 142 | 219 | 124 |
| Add | 7 | 59 | 126 | 9 | 56 | 136 | 9 | 78 |
| Del | 38 | 57 | 115 | 13 | 56 | 146 | 0 | 78 |
| Correction | 138 | 153 | 439 | 124 | 165 | 424 | 228 | 280 |

As previously discussed in Fig. [3(a)](https://arxiv.org/html/2503.05488v2#S3.F3.sf1), the disparity in the conceptualization of KIE errors (either as {FP, FN} or as correction cost) results in assessment of KIE models that is misaligned with industrial applications. Table [3](https://arxiv.org/html/2503.05488v2#S6.T3) shows distinctive gap between the $FP+FN$ and Correction Cost values consistent across all models and datasets. Our work, brings to light of this discrepancy and proposes KIEval${}_{\text{Aligned}}$ formulation to better align KIE evaluation to application settings.

## 7 KIE Evaluation for RPA System

Figure: Figure 7: In CORD, Donut’s KIEval${}_{\text{Aligned}}$ and KIEval${}_{\text{Aligned}}^{\tau}$ in relation to varying confidence score thresholds, $\tau$, alongside the corresponding automation rates, auto-rate^τ. Increase in confidence score thresholds leads to an increase in KIEval${}_{\text{Aligned}}^{\tau}$, while the automation rate decreases due to the rising number of entities requiring human revision.
Refer to caption: x9.png

In addition to the inclusion of structural relation and alignment of metric formulation, there exists a distinctive factor of human-correction that warrants attention when evaluating KIE models in RPA systems. Irrespective of the KIE model’s training, it is improbable to consistently achieve error-free extraction performance across a diverse range of documents. In view of this improbability, human-correction (correction by human-intervention) is commonly adopted by RPA systems. Human-correction however, requires a method for selecting a subset of predictions, as verifying and correcting all extracted information is impractical and undermines the very goal of automation in RPA.

Existing RPA systems commonly adopt confidence score based correction where information extracted with confidence below a specific threshold (i.e. uncertain) is selected for verification and correction (if necessary). Selection of optimal threshold value is an application-specific decision that differs from one RPA system to another, contingent on the system’s inclinations to trade-off automation rate for KIE performance. In this work, we demonstrate this trade-off analysis with KIEval and highlighting its added insights over prior metrics.

We propose a method to analyse this trade-off in terms of post-correction KIE performance, automation rate, and confidence score threshold value, $\tau$. We first define the automation rate, auto-rate^τ, which reflects the proportion of model predictions processed without human verification, interpreted as the number of entities with a confidence score higher than $\tau$. Post-correction KIE performance, KIEval${}_{\text{Aligned}}^{\tau}$, denotes the final KIE performance after KIE predictions with confidence scores below $\tau$ are verified and corrected by humans. A formal definition of these two formulations is provided in the Appendix C.

Fig. [7](https://arxiv.org/html/2503.05488v2#S7.F7) presents the auto-rate^τ and KIEval${}_{\text{Aligned}}^{\tau}$ as a function of the confidence score threshold, $\tau$ in Donut’s performance on CORD. The trade-off trend depicted in Fig. [7](https://arxiv.org/html/2503.05488v2#S7.F7) indicates that, as the threshold value increases, the number of information extracted requiring human review increases, leading to a higher post-correction KIE score at the cost of reduced automation rate. Incorporating such trade-off analysis in evaluation of KIE models not only provides deeper insights but also enables stakeholders to conduct cost-benefit evaluations effectively and determine the optimal threshold value for their RPA system.

## 8 Conclusion

In this work, we bring to light of the discrepancies between the existing Document KIE evaluation metrics and the key consideration factors of industrial settings, such as RPA systems. We identify the challenges behind these discrepancies and propose KIEval, metric formulated with an application-centric design. Specifically, KIEval leverages group matching data between the predictions and ground-truth groupings to integrate structural relations in KIE evaluations, differentiating itself from prior metrics that lack grouping awareness in evaluation. Additionally, KIEval formulates KIE errors in terms of the corrections incurred in automation systems (i.e. Substitution, Addition, or Deletion) further bridging the gap between the evaluation metric and industrial settings. The experiments not only verify these discrepancies in existing metrics but also shows how KIEval provides a different perspective of KIE model evaluation from the industrial application’s standpoint. On top of these discrepancies, we also demonstrate an application use-case scenario that illustrates the valuable insights which the trade-off analysis brings to RPA systems. This aspect has been overlooked in prior Document KIE metrics. We believe that KIEval could serve as a standard evaluation metric for various KIE tasks and encourage the research community to focus on solving the remaining challenges in KIE tasks with the industrial application in mind.

## References

- [1]
Appalaraju, S., Jasani, B., Kota, B.U., Xie, Y., Manmatha, R.: Docformer: End-to-end transformer for document understanding. In: Proceedings of the IEEE/CVF international conference on computer vision. pp. 993–1003 (2021)
- [2]
Biten, A.F., Tito, R., Mafla, A., Gomez, L., Rusinol, M., Mathew, M., Jawahar, C., Valveny, E., Karatzas, D.: Icdar 2019 competition on scene text visual question answering. In: 2019 International Conference on Document Analysis and Recognition (ICDAR). pp. 1563–1570. IEEE (2019)
- [3]
Chen, Z., Wang, W., Cao, Y., Liu, Y., Gao, Z., Cui, E., Zhu, J., Ye, S., Tian, H., Liu, Z., et al.: Expanding performance boundaries of open-source multimodal models with model, data, and test-time scaling. arXiv preprint arXiv:2412.05271 (2024)
- [4]
Dosovitskiy, A., Beyer, L., Kolesnikov, A., Weissenborn, D., Zhai, X., Unterthiner, T., Dehghani, M., Minderer, M., Heigold, G., Gelly, S., et al.: An image is worth 16x16 words: Transformers for image recognition at scale. In: International Conference on Learning Representations (2020)
- [5]
Garncarek, Ł., Powalski, R., Stanisławek, T., Topolski, B., Halama, P., Turski, M., Graliński, F.: Lambert: Layout-aware language modeling for information extraction. In: International Conference on Document Analysis and Recognition. pp. 532–547. Springer (2021)
- [6]
He, J., Wang, L., Hu, Y., Liu, N., Liu, H., Xu, X., Shen, H.: Icl-d3ie: In-context learning with diverse demonstrations updating for document information extraction. arxiv 2023. arXiv preprint arXiv:2303.05063
- [7]
He, K., Zhang, X., Ren, S., Sun, J.: Deep residual learning for image recognition. In: Proceedings of the IEEE conference on computer vision and pattern recognition. pp. 770–778 (2016)
- [8]
Hong, T., Kim, D., Ji, M., Hwang, W., Nam, D., Park, S.: Bros: A pre-trained language model focusing on text and layout for better key information extraction from documents. In: Proceedings of the AAAI Conference on Artificial Intelligence. vol. 36, pp. 10767–10775 (2022)
- [9]
Huang, Y., Lv, T., Cui, L., Lu, Y., Wei, F.: Layoutlmv3: Pre-training for document ai with unified text and image masking. In: Proceedings of the 30th ACM International Conference on Multimedia. pp. 4083–4091 (2022)
- [10]
Hwang, W., Yim, J., Park, S., Yang, S., Seo, M.: Spatial dependency parsing for semi-structured document information extraction. arXiv preprint arXiv:2005.00642 (2020)
- [11]
Jaume, G., Ekenel, H.K., Thiran, J.P.: Funsd: A dataset for form understanding in noisy scanned documents. In: 2019 International Conference on Document Analysis and Recognition Workshops (ICDARW). vol. 2, pp. 1–6. IEEE (2019)
- [12]
Kim, G., Hong, T., Yim, M., Nam, J., Park, J., Yim, J., Hwang, W., Yun, S., Han, D., Park, S.: Ocr-free document understanding transformer. In: European Conference on Computer Vision. pp. 498–517. Springer (2022)
- [13]
Lee, K., Joshi, M., Turc, I.R., Hu, H., Liu, F., Eisenschlos, J.M., Khandelwal, U., Shaw, P., Chang, M.W., Toutanova, K.: Pix2struct: Screenshot parsing as pretraining for visual language understanding. In: International Conference on Machine Learning. pp. 18893–18912. PMLR (2023)
- [14]
Li, C., Bi, B., Yan, M., Wang, W., Huang, S., Huang, F., Si, L.: Structurallm: Structural pre-training for form understanding. In: Proceedings of the 59th Annual Meeting of the Association for Computational Linguistics and the 11th International Joint Conference on Natural Language Processing (Volume 1: Long Papers). pp. 6309–6318 (2021)
- [15]
OpenAI: Gpt-4v(ision) system card (2023)
- [16]
Park, S., Shin, S., Lee, B., Lee, J., Surh, J., Seo, M., Lee, H.: Cord: a consolidated receipt dataset for post-ocr parsing. In: Workshop on Document Intelligence at NeurIPS 2019 (2019)
- [17]
Peng, Q., Pan, Y., Wang, W., Luo, B., Zhang, Z., Huang, Z., Hu, T., Yin, W., Chen, Y., Zhang, Y., et al.: Ernie-layout: Layout knowledge enhanced pre-training for visually-rich document understanding. arXiv preprint arXiv:2210.06155 (2022)
- [18]
Powalski, R., Borchmann, Ł., Jurkiewicz, D., Dwojak, T., Pietruszka, M., Pałka, G.: Going full-tilt boogie on document understanding with text-image-layout transformer. In: Document Analysis and Recognition–ICDAR 2021: 16th International Conference, Lausanne, Switzerland, September 5–10, 2021, Proceedings, Part II 16. pp. 732–747. Springer (2021)
- [19]
Tito, R., Mathew, M., Jawahar, C., Valveny, E., Karatzas, D.: Icdar 2021 competition on document visual question answering. In: Document Analysis and Recognition–ICDAR 2021: 16th International Conference, Lausanne, Switzerland, September 5–10, 2021, Proceedings, Part IV 16. pp. 635–649. Springer (2021)
- [20]
Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A.N., Kaiser, Ł., Polosukhin, I.: Attention is all you need. Advances in neural information processing systems 30 (2017)
- [21]
Wang, J., Jin, L., Ding, K.: Lilt: A simple yet effective language-independent layout transformer for structured document understanding. In: Proceedings of the 60th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers). pp. 7747–7757 (2022)
- [22]
Wang, P., Bai, S., Tan, S., Wang, S., Fan, Z., Bai, J., Chen, K., Liu, X., Wang, J., Ge, W., Fan, Y., Dang, K., Du, M., Ren, X., Men, R., Liu, D., Zhou, C., Zhou, J., Lin, J.: Qwen2-vl: Enhancing vision-language model’s perception of the world at any resolution. arXiv preprint arXiv:2409.12191 (2024)
- [23]
Xu, Y., Xu, Y., Lv, T., Cui, L., Wei, F., Wang, G., Lu, Y., Florencio, D., Zhang, C., Che, W., et al.: Layoutlmv2: Multi-modal pre-training for visually-rich document understanding. arXiv preprint arXiv:2012.14740 (2020)
- [24]
Xu, Y., Li, M., Cui, L., Huang, S., Wei, F., Zhou, M.: Layoutlm: Pre-training of text and layout for document image understanding. In: Proceedings of the 26th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining. pp. 1192–1200 (2020)
- [25]
Xu, Y., Lv, T., Cui, L., Wang, G., Lu, Y., Florencio, D., Zhang, C., Wei, F.: Xfund: A benchmark dataset for multilingual visually rich form understanding. In: Findings of the Association for Computational Linguistics: ACL 2022. pp. 3214–3224 (2022)
- [26]
Yu, W., Zhang, C., Cao, H., Hua, W., Li, B., Chen, H., Liu, M., Chen, M., Kuang, J., Cheng, M., et al.: Icdar 2023 competition on structured text extraction from visually-rich document images. arXiv preprint arXiv:2306.03287 (2023)
- [27]
Zhang, J., You, Z., Wang, J., Le, X.: Sail: Sample-centric in-context learning for document information extraction. arXiv preprint arXiv:2412.17092 (2024)

## Appendix 0.A Datasets

The following table provides details on the datasets and models used in the experiments conducted in this paper. All datasets and models are available on Hugging Face to ensure experimental reproducibility.

**Table 4: Hugging Face Models and Datasets used in the experiments.**
|  | LayoutXLM | LayoutLMv3 | Donut |
| --- | --- | --- | --- |
| Models | microsoft/layoutxlm-base | microsoft/layoutlmv3-base | naver-clova-ix/donut-base |
| SROIE | darentang/sroie | podbilabs/sroie-donut |  |
| CORD | nielsr/cord-layoutlmv3 | naver-clova-ix/cord-v2 |  |
| FUNSD | nielsr/funsd-layoutlmv3 | - |  |

## Appendix 0.B Multimodal LLM prompt for CORD KIE

Following prompt is used when experimenting with GPT-4o, Qwen2-VL and InternVL 2.5 for KIE in the CORD dataset. Arrow symbol $\hookrightarrow$ represents new-line wrapping in the following text.

You will be provided with a receipt as an image.Your task is to analyze the receipt carefully and extract keyinformation from it.The entities to be extracted along with their descriptions areprovided below.| Category | Sub-Category (if applicable) | Entity | Description || --- | --- | --- | --- || menu | (not applicable) | menu.cnt | quantity of menu ||      | (not applicable) | menu.discountprice | discounted price of menu ||      | (not applicable) | menu.etc | others ||      | (not applicable) | menu.itemsubtotal | price of each menu after discount applied ||      | (not applicable) | menu.nm | name of menu ||      | (not applicable) | menu.num | identification # of menu ||      | (not applicable) | menu.price | total price of menu ||      | sub | menu.sub_cnt | quantity of submenu ||      | sub | menu.sub_nm | name of submenu ||      | sub | menu.sub_price | total price of submenu ||      | sub | menu.sub_unitprice | unit price of submenu ||      | (not applicable) | menu.unitprice | unit price of menu ||      | (not applicable) | menu.vatyn | whether the price includes tax or not || sub_total |  (not applicable) | sub_total.discount_price | discounted price in total ||          |  (not applicable) | sub_total.etc | others ||          |  (not applicable) | sub_total.service_price | service charge ||          |  (not applicable) | sub_total.subtotal_price | subtotal price ||          |  (not applicable) | sub_total.tax_price | tax amount || total | (not applicable) | total.cashprice | amount of price paid in cash ||       | (not applicable) | total.changeprice | amount of change in cash ||       | (not applicable) | total.creditcardprice | amount of price paid in credit/debit card ||       | (not applicable) | total.emoneyprice | amount of price paid in emoney, point ||       | (not applicable) | total.menuqty_cnt | total count of quantity ||       | (not applicable) | total.menutype_cnt | total count of type of menu ||       | (not applicable) | total.total_etc | others ||       | (not applicable) | total.total_price | total price |Each entity (e.g. menu.cnt) is part of a category (e.g. menu).You are to extract the entities from the receipt and return in the following format:```json{{    "menu": <dictionary or list of dictionaries>,    "sub_total": <dictionary or list of dictionaries>,    "total": <dictionary or list of dictionaries>}}```Note the following characteristics:1. All entities falling under the same category should be grouped together (represented as a dictionary, such as {total.cashprice, total.changeprice, ...}).2. If there are multiple entities of the same category, they should be represented as a list of dictionaries.3. If an entity is not present in the receipt, it should be excluded from the dictionary.4. Each of the entity’s value should either be a string or a list of strings.5. Note that menu.sub represents a sub-category of the menu category. As such, all entities under menu.sub should be grouped together (either dictionary or list of dictionaries) under the same menu group.6. You are to respond in JSON format only and ensure that the keys in the dictionary are exactly the same as the entities provided above.7. If you are unable to extract any information, please return an empty list for that category.Here is an example of the expected return format:```json{  "menu": [    {      "menu.nm": "SPGTHY BOLOGNASE",      "menu.cnt": "1",      "menu.price": "58,000"    },    {      "menu.nm": "PEPPER AUS",      "menu.cnt": "1",      "menu.price": "165,000",      "menu.sub": {        "menu.sub_nm": "WELL DONE"      }    },    {      "menu.nm": "WAGYU RIBEYE",      "menu.cnt": "1",      "menu.price": "195,000",      "menu.sub": {        "menu.sub_nm": "MEDIUM WELL"      }    }  ],  "sub_total": {    "sub_total.subtotal_price": "503,000",    "sub_total.service_price": "25,150",    "sub_total.tax_price": "52,815"  },  "total": {    "total.total_price": "580,965"  }}```

## Appendix 0.C Automation Trade-off Analysis Metric

Prior metrics, including $\text{KIEval}_{\text{Aligned}}$ defined above, evaluate Document KIE models without consideration of the full pipeline of Document KIE applications. The RPA system commonly employs a human-correction stage after model inference. Specifically, the RPA system utilizes confidence scores of the extracted entities by a Document KIE model and identifies which entities require further manual verification and corrections with a certain threshold, $\tau$, of the confidence score. We assume that human correction is only conducted on the predictions with lower confidence scores and considers only substitution and deletion without any addition operations because addition operation usually requires examining all predictions and ground-truths, making the correction process and the RPA system inefficient.

To illustrate the formulation, let $c(\text{pr}_{n,i})$ be the confidence score of $\text{pr}_{n,i}$, where $\text{pr}_{n,i}$ indicates the $i$-th entity in the $n$-th predicted group. $\mathbf{PR}^{<\tau}$ is the set of the predictions of which confidence scores are less than the threshold $\tau$. Since $\mathbf{PR}^{<\tau}$ is only reviewed among the total $\mathbf{PR}$, the automation rate of the RPA system can be defined as follows:

$$ ${\text{auto-rate}}^{\tau}=1-{|\mathbf{PR}^{<\tau}|}/{|\mathbf{PR}|}.$ (13) $$

If the automation rate becomes close to 0 with high $\tau$, the system becomes inefficient but the output of the system becomes accurate. When the automation rate is close to 1 with sufficiently low $\tau$, the system becomes efficient but at the cost of potentially containing incorrect predictions by skipping the human-correction stage.

To control the trade-off between the system efficiency and accuracy, we introduce KIEval${}_{\text{Aligned}}^{\tau}$ that evaluates the accuracy of the RPA automation system with the human-correction stage. The evaluation assumes no human error in the correction stage and the errors in $\mathbf{PR}^{<\tau}$ are only revised with substitution and deletion operations. After the correction process, the remaining errors can be categorized into $\text{Subs}^{\tau}$, $\text{Del}^{\tau}$, and Add. $\text{Subs}^{\tau}$ and $\text{Del}^{\tau}$ denote the error present in predictions with confidence score higher than $\tau$, while Add represents the number of required entities missed in $\mathbf{PR}$. With the remaining error counts, KIEval${}_{\text{Aligned}}^{\tau}$ can be calculated as follows:

$$ $\text{KIEval}_{\text{Aligned}}^{\tau}=1-\frac{\text{Subs}^{\tau}+\text{Del}^{ \tau}+\text{Add}}{\text{N}(\mathbf{PR}^{*})+\text{Add}},$ (14) $$

where $\text{N}(\mathbf{PR}^{*})$ indicates the number of predictions, $\mathbf{PR}^{*}$, after the human correction stage. The denominator includes Add to represent the total number of entities of the system output, including the entities missing in $\mathbf{PR}^{*}$. Through ${\text{auto-rate}}^{\tau}$ and KIEval${}_{\text{Aligned}}^{\tau}$, the automation efficiency and accuracy of the RPA system can be measured by adjusting the confidence threshold $\tau$, facilitating their trade-off analysis in Document KIE.