KIEval: Evaluation Metricfor Document Key Information Extraction
Minsoo Khang, Sang Chul Jung, Sungrae Park, and Teakgyu Hong 
Upstage AI, South Korea
26 Maret 2025

Abstract. 
Document Key Information Extraction (KIE) is a technol-ogy that transforms valuable information in document images into struc-tured data, and it has become an essential function in industrial settings.However, current evaluation metrics of this technology do not accuratelyreﬂect the critical attributes of its industrial applications. In this pa-per, we present KIEval, a novel application-centric evaluation metric forDocument KIE models. Unlike prior metrics, KIEval assesses DocumentKIE models not just on the extraction of individual information (entity)but also of the structured information (grouping). Evaluation of struc-tured information provides assessment of Document KIE models thatare more reﬂective of extracting grouped information from documentsin industrial settings. Designed with industrial application in mind, webelieve that KIEval can become a standard evaluation metric for devel-oping or applying Document KIE models in practice. The code will bepublicly available.

## 4 KIEval

### 4.1 Structured Evaluation – Entity and Group Level

In KIEval, to integrate structural relation into the KIE evaluation, *group-matching* was conducted between the predicted and ground-truth key-value pairs prior to entity-level and group-level evaluations. While variant of *group-matching* for entity-level evaluation was employed in [10], the lack of formal definition underscores its significance in the view of KIE metric standardisation. To illustrate, let $\mathbf{PR} = \{\text{pr}_1, \text{pr}_2, \dots, \text{pr}_N\}$ be a set of predicted groups and $\mathbf{GT} = \{\text{gt}_1, \text{gt}_2, \dots, \text{gt}_M\}$ be ground-truth groups, where each group consists of a set of entities represented by tuples, (entity-type, value). The non-group entities (i.e. company.name and company.number in receipt) are included in 1-st group to represent all entities with the same structural format. For the formal definition of *group-matching*, we define a matching score $S_{(n,m)}$ counting the identical entities between $\text{pr}_n$ and $\text{gt}_m$. Based on the matching scores between groups, each prediction group is matched with a ground-truth group through Hungarian matching to obtain a group-matched set of groups, $\mathbf{G} = \{(n_1, m_1), (n_2, m_2), \dots\}$, where $n_g$ and $m_g$ indicate the $g$-th matched indices of predicted and ground-truth groups, respectively, and $|\mathbf{G}|$ results as $\min(N, M)$. The group-matching can be defined as follows:

$$\mathbf{G} = \text{Hungarian}(\mathbf{PR}, \mathbf{GT}, \mathbf{S}) \tag{1}$$

where $\mathbf{S}$ indicates a set of matching scores, $S_{(n,m)}$, between all pairs between predictions and ground-truth. For an entity $e$ at a matching $(n, m)$, F1 statistics such as True-Positive ($TP$), False-Negative ($FN$), and False-Positive ($FP$) can be calculated as follows;

$$TP^e_{(n,m)} = S^e_{(n,m)}, \quad FN^e_{(n,m)} = \text{N}_e(\text{gt}_m) - S^e_{(n,m)}, \quad FP^e_{(n,m)} = \text{N}_e(\text{pr}_n) - S^e_{(n,m)} \tag{2}$$

where $S^e_{(n,m)}$ indicates the number of identical entity pairs, which has entity-type $e$ between $n$-th predicted and $m$-th ground-truth groups. The $\text{N}_e(\cdot)$ represents the operation counting entity-type $e$ in a group. In other words, $TP^e_{(n,m)}$ indicates the matched entity, and $FN^e_{(n,m)}$ and $FP^e_{(n,m)}$ represent the remaining ground-truths and predictions in the specific match $(n, m)$ in terms of entity type $e$, respectively. To calculate a final cumulated score, *KIEval Entity F1*, the total F1 statistics are identified as follows:

$$TP^{\text{entity}} = \sum_{(n,m) \in \mathbf{G}} \sum_{e} TP^e_{(n,m)} \tag{3}$$

$$FN^{\text{entity}} = \sum_{m=1}^{M} \sum_{e} \text{N}_e(\text{gt}_m) - TP^{\text{entity}} \tag{4}$$

$$FP^{\text{entity}} = \sum_{n=1}^{N} \sum_{e} \text{N}_e(\text{pr}_n) - TP^{\text{entity}} \tag{5}$$

The statistics can be used to calculate *KIEval Entity F1* metric using standard precision and recall manners.

Group-level evaluation, *KIEval Group F1*, is also conducted on the group-matched $\mathbf{G}$ where F1 statistics are evaluated across different groups. Unlike *KIEval Entity F1* which treats all entities in a group as a unit of information to evaluate F1 statistics, *KIEval Group F1* evaluates on the entire group as a unit of information. It should be noted that, group-level evaluation is conducted on all but the first element of $\mathbf{G}$ (i.e. $\mathbf{G}'$) as the first element represent non-group entities.

$$\mathbf{G}' = \mathbf{G} \setminus (n_1, m_1) \tag{6}$$

$$TP^{\text{group}} = \sum_{(n,m) \in \mathbf{G}'} \mathbb{1}[S^e_{(n,m)} = \text{N}_e(\text{gt}_m) = \text{N}_e(\text{pr}_n) \quad \forall e] \tag{7}$$

Eq. 7 shows formulation of group-level True-Positive measure where counting identical pairs of prediction and ground truth groups in $\mathbf{G}'$. In the equation, $\mathbb{1}[\cdot]$ indicates a binary operator providing 1 when the predicted and ground-truth groups are identical. FN and FP are calculated by counting the remaining ground-truth and predicted groups, respectively. Finally, *KIEval Group F1* can be identified with the same precision and recall fashion. Based on the formal definition of *KIEval Entity F1* and *KIEval Group F1* above, both formulations aim to incorporate structure relation assessment in evaluation at the entity and group-level, respectively.

### 4.2 Aligned Metric Formulation

While distinction of model’s erroneous prediction and missed prediction as FP and FN in metric formulation could be well-suited from the model-centric point-of-view, its misalignment in the standpoint of industrial application has motivated the formulation of our metric. KIEval’s application-centric design addresses this misalignment by conceptualizing KIE errors as correction costs incurred in application settings. *Correction* refers to one of the three editing steps: substitution, addition, and deletion of prediction values to match the ground-truth. For an entity $e$ at the matching condition $(n,m) \in \mathbf{G}$, the steps can be defined in terms of FN and FP as follows:

$$\text{Subs}^e_{(n,m)} = \min(FP^e_{(n,m)}, FN^e_{(n,m)}) \tag{8}$$

$$\text{Add}^e_{(n,m)} = FN^e_{(n,m)} - \text{Subs}^e_{(n,m)} \tag{9}$$

$$\text{Del}^e_{(n,m)} = FP^e_{(n,m)} - \text{Subs}^e_{(n,m)} \tag{10}$$

As can be seen, the substitution is defined as the minimum number of $FP^e_{(n,m)}$ and $FN^e_{(n,m)}$, which indicates the number of predictions that require modifications to match corresponding ground-truth values. The addition and deletion are the number of remaining $FN^e_{(n,m)}$ and $FP^e_{(n,m)}$, respectively. The number of error, $\text{Error}^e_{(n,m)} = \text{Subs}^e_{(n,m)} + \text{Add}^e_{(n,m)} + \text{Del}^e_{(n,m)}$, is represented by summing the three error corrections. The total number of error can be defined as follows;

$$\text{Error} = \sum_{(n,m) \in \mathbf{G}} \sum_{e} \text{Error}^e_{(n,m)} + \underbrace{\sum_{(*,m) \notin \mathbf{G}} \sum_{e} \text{N}_e(\text{gt}_m)}_{\text{Add unmatched gt}} + \underbrace{\sum_{(n,*) \notin \mathbf{G}} \sum_{e} \text{N}_e(\text{pr}_n)}_{\text{Del unmatched pr}} \tag{11}$$

Here, the first term on the right-hand side indicates the number of error corrections in the group match condition $\mathbf{G}$, and the second and third terms represent the number of additions and deletions, respectively, for the non-matched groups. Finally, $\text{KIEval}_{\text{Aligned}}$ is calculated with the Error and the number of correct values, $TP$. The following equation shows the formulation;

$$\text{KIEval}_{\text{Aligned}} = \frac{TP^{\text{entity}}}{TP^{\text{entity}} + \text{Error}} \tag{12}$$

The $\text{KIEval}_{\text{Aligned}}$ not only better aligns with industrial applications, but also benefits from high interpretability due to its formulations in terms of well-known F1 components: TP, FP, and FN.