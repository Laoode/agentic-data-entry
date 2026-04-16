## Contents
- 1 Introduction
- 2 Related Work
  - Metrics
  - LLMs for Document Processing
- 3 Metric Definition
  - 3.1 Supported data types
  - 3.2 Formal definition of the ANLS* metric
    - 3.2.1 Definition of the score s 𝑠 s italic_s
    - 3.2.2 Definition of the length l 𝑙 l italic_l
- 4 Experimental Evaluation
  - 4.1 Examples
  - 4.2 Experimental Evaluation
    - QA prompt
    - Information extraction prompt
    - GLLM Comparison
    - Different Prompting Methods
    - GLLMs with Vision Capabilities
    - Comparison with DocLLM
    - Open-source Models
- 5 Conclusion & Discussion
- References

## Abstract

Abstract Traditionally, discriminative models have been the predominant choice for tasks like document classification and information extraction. These models make predictions that fall into a limited number of predefined classes, facilitating a binary true or false evaluation and enabling the direct calculation of metrics such as the F1 score. However, recent advancements in generative large language models (GLLMs) have prompted a shift in the field due to their enhanced zero-shot capabilities, which eliminate the need for a downstream dataset and computationally expensive fine-tuning. However, evaluating GLLMs presents a challenge as the binary true or false evaluation used for discriminative models is not applicable to the predictions made by GLLMs. This paper introduces a new metric for generative models called ANLS* for evaluating a wide variety of tasks, including information extraction and classification tasks. The ANLS* metric extends existing ANLS metrics as a drop-in-replacement and is still compatible with previously reported ANLS scores. An evaluation of 7 different datasets, 6 different GLLMs and 3 different prompting methods using the ANLS* metric is also provided, demonstrating the importance of the proposed metric. We also benchmark a novel approach to generate prompts for documents, called SFT, against other prompting techniques such as LATIN. In 27 out of 35 cases, SFT outperforms other techniques and improves the state-of-the-art, sometimes by as much as 18 18 18 18 percentage points. Sources are available at https://github.com/deepopinion/anls_star_metric

## 1 Introduction

The increases in model size, dataset size, and available compute have significantly advanced the state-of-the-art (SOTA) on many natural language processing (NLP) tasks [7, 4, 13, 12]. A unique and challenging domain within NLP is document processing, because documents contain text, images and tables and are, therefore, inherently multimodal. Additionally, the text is not strictly arranged in a linear fashion, but often has distinct positional structure within the 2D space of the document (i.e. the layout of the document). As such, document processing tasks are often addressed with specialized layout models [29, 28, 5] that improve the performance by encoding important 2D positional information of bounding boxes together with the text tokens.

While discriminative models such as LayoutLMv3 [5] have significantly advanced the state-of-the-art in document processing tasks, they still possess certain limitations. For instance, they are incapable of executing tasks that require additional synthesis, translation, or enhancement of text, as they cannot generate tokens and usually only label tokens. For example, a task may require extracting the date-time and transforming it into the YYYY-MM-DD format. Consequently, generative large language models (GLLMs) have garnered considerable attention in this field in recent times [25] as they can solve these problems without the need for additional post-processing steps. Furthermore, these models are usually pre-trained on large datasets, eliminating the need for fine-tuning them on a specific downstream task as is usually done for classical deep learning models [29, 28, 5]. Simply altering the input prompt (zero-shot) or providing a few examples demonstrating the task (few-shot) is sufficient to accomplish a task with decent performance. This is particularly crucial for document processing tasks, as the number of available datasets is limited and the creation of new ones is costly. Consequently, the community is moving towards large generative models for document processing tasks [25, 26].

While the evaluation of discriminative models typically relies on measuring the F1 score by counting correctly labeled bounding boxes coming from an OCR solution, this method is not applicable for GLLMs since the extracted, and possibly already pre-processed, information is directly returned as generated text. I.e. there is no direct connection between the OCR bounding boxes and the extracted information anymore. Generated text may also contain minor errors such as typos, which should be penalized differently compared to completely wrong answers. GLLMs are, therefore, typically evaluated using the Average Normalized Levenshtein Similarity (ANLS) metric [3], which is a normalized form of the Levenshtein similarity, assessing the closeness of a generated answer to the expected output. A shortcoming of the ANLS metric is that it can only deal with strings and lists, but cannot be used for dictionaries or any combination of types that are often encountered when dealing with information extraction tasks. Additionally, some tasks require to extract information with a list structure such as line-item extraction [14], which requires the evaluation of complex output objects.

In this paper, we introduce ANLS*, a metric that can be used to evaluate a wide variety of tasks such as information extraction or classification, even in cases where output values that may contain minor errors are generated. It is worth mentioning, that this metric can also be used for discriminative models which allows for direct comparison of both discriminative and generative models with one single metric in the future. Additionally, the ANLS* metric can be applied to unstructured as well as structured outputs or any combination of both which makes it a versatile tool for the evaluation of document processing tasks. The proposed metric extends all previously defined ANLS metrics [3]. That is, results that could be calculated using the ANLS metric remain unchanged under ANLS*, while simultaneously offering greater flexibility. Therefore, it serves as a plug-in replacement for existing ANLS metrics.

Lastly, we provide qualitative as well as quantitative experiments using the proposed ANLS* metric to demonstrate the importance of the proposed metric. Various GLLMs and prompting methods across different datasets are evaluated with the proposed metric. Those results are not only provided for the community as a baseline for future experiments, but the scripts to reproduce the results are also publicly available.

## 2 Related Work

##### Metrics

The normalized Levenshtein similarity (NLS) was defined by Levenshtein et al. [10] to measure the similarity between words using the minimal distance between those words. Later, the Average Normalized Levenshtein Similarity (ANLS) was introduced by Biten et al. [3] for the evaluation of visual question-answering (VQA) tasks. The ANLS metric takes OCR errors into consideration, which makes it suitable for generative models. Tito et al. [20] further expanded the ANLS metric for the comparison of lists by using the Hungarian matching algorithm from Kuhn [9] to find the best match between the ground truth list and the predicted list. Finally, Van Landeghem et al. [22] extended the normalized Levenshtein similarity to account for predictions that should be null. This metric is not only useful for verifying the correct handling of unanswerable questions but also for penalizing hallucinations generated by GLLMs.

##### LLMs for Document Processing

Xu et al. [29] introduced a novel layout-aware language model to encode bounding box information as well as visual information about the document in tokens in order to improve document processing tasks. They outperformed purely text-based models such as BERT [4] by a large margin. Novel developments with different attention layers and pre-training methods have later been introduced [28, 5]. A novel GLLM called DocLLM was introduced by Wang et al. [25] specifically for document processing tasks. This model captures cross-alignment between text and spatial modalities decomposing the attention mechanism of transformers. Although they could show significant improvements and novel pre-training methods, we will demonstrate that this model is still behind extremely large, purely text-based models, such as gpt-4 [2]. As a consequence, special prompting mechanisms that may encode OCR scanned documents in a way that is easier to understand by purely text-based models gained interest recently. Wang et al. [26] introduced such a prompting technique, called LATIN, to enhance the representation of documents for text-based GLLMs. Instead of directly encoding positional information in the tokens, they utilized layout-aware instruction prompts by using the positional information of the bounding boxes after the OCR scan. We developed a more advanced approach, called SFT that takes several properties of documents and LLMs into account. We will show that SFT is superior to LATIN and other prompting techniques. (^1^11The scope of this paper does not include an introduction of SFT. It may be introduced in a future publication.)

Other approaches completely bypass the conversion from OCR to prompts by employing a multimodal model that directly processes documents without a separate OCR step. For instance, Kim et al. [8] developed an OCR-free document transformer architecture. Ye et al. [30] developed a generative multimodal model named MPlug-DocOWL that was trained on language-only, general vision-and-language, and document instruction tuning datasets.

## 3 Metric Definition

In this section, we introduce ANLS*. The goal is to develop a metric that is not only compatible with the existing ANLS [3] and the ANLSL [20] metrics, but also penalizes unanswerable questions in case they are answered as proposed by Van Landeghem et al. [22]. Additionally, the ANLS* metric should be a tool that is applicable for a wide variety of tasks, including tasks with dictionary outputs, lists or any combination of those in order to handle e.g. line-item extraction [14] as well as simple question-answering tasks. As a result, the ANLS* metric serves as a direct drop-in replacement for all standard ANLS metrics defined by the community so far, and can additionally be used for evaluating all document-processing tasks.

### 3.1 Supported data types

The ANLS* metric supports the following data types:

- 1.
String - To compare strings against each other using the normalized Levenshtein similarity.
- 2.
None - Sometimes questions are not answerable. With this type it can be checked, whether the model does not answer. Any answer other than None will be penalized.
- 3.
Tuple - Compare the given answer with each element in the tuple and select the element that produces the maximum ANLS* score. This is also provided by the classical ANLS metric [3].
- 4.
List - Sometimes it is required to extract information in the form of lists from a document. For example, extracting all purchased items found in an invoice. While the order is not important, the list should contain all items. Note that the same item can occur multiple times in lists. Hungarian matching [9] is used to compare the ground truth and the predicted list against each other. Both, missing elements as well as hallucinated elements, are penalized as introduced by Tito et al. [20].
- 5.
Dict - For document information extraction it is usually required to extract key-value pairs. For example, when extracting the date and total value from an invoice. Missing keys as well as hallucinated keys are penalized.

Figure 1: Tree Structure Decomposition for ANLS* Evaluation:
---

(a) Ground Truth

```json
{
  "date": Tuple("31.12.2023", "31.Dec 2023"),  // Multiple valid predictions
  "prices": List("21.50", "5.99"),
  "id": None,
}
```

**Tree Structure:**
```
              Dict
           /    |    \
      date    prices   id
      Tuple    List
      /  \     /  \      \
"31.12.2023" "31.Dec 2023" "21.50" "5.99"  None
```

---

(b) Prediction with ANLS* = 1.0 ✅

```json
{
  "date": "31.12.2023",
  "prices": List("5.99", "21.50"),
}
```

**Tree Structure:**
```
           Dict
          /    \
       date   prices
       String   List
         |      /  \
  "31.12.2023" "5.99" "21.50"
```

> ✅ Correct prediction — matches ground truth within valid tuple alternatives and list order tolerance.

---

(c) Prediction with ANLS* < 1.0 ❌

```json
{
  "date": "31.12.2022",
  "prices": List("5.99", "21.50", "27.49"),
  "id": "2022",
}
```

**Tree Structure:**
```
                Dict
           /     |      \
        date   prices   [id]  ← hallucinated
       String   List      \
         |     /   \   \     "2022"  ← incorrect
  "31.12.2022" "5.99" "21.50" ["27.49"]
                               ↑ hallucinated
```

> ❌ Partially incorrect — wrong date year (`2022` vs `2023`), hallucinated price `"27.49"`,
> and hallucinated `id` field with value `"2022"`. Red nodes indicate incorrect/hallucinated values.

---
**Figure 1:** Examples of how the ground truth, as well as predictions, are decomposed into a tree structure. A correct prediction is shown in Figure 1b, while Figure 1c visualizes a partially incorrect prediction. It's worth mentioning that any hallucination as well as incorrect types are penalized as well. More examples are given in **Table 1**.
```

It is worth mentioning that all combinations of the above types are supported as well. For example, a dictionary may contain lists of strings or the elements of a list may be dictionaries. The implementation of the ANLS* metric maps those complex structures into a tree and compares the ground truth tree against the predicted tree from the model. [0(a)](https://arxiv.org/html/2402.03848v3#S3.F0.sf1) visualizes how the ground truth is decomposed into a tree structure that can then be compared against predictions for an example.

[0(b)](https://arxiv.org/html/2402.03848v3#S3.F0.sf2) demonstrates a prediction with $\text{ANLS*}=1.0$ w.r.t [0(a)](https://arxiv.org/html/2402.03848v3#S3.F0.sf1).
Finally, [0(c)](https://arxiv.org/html/2402.03848v3#S3.F0.sf3) shows an example of a partially incorrect prediction. Note that the ANLS* metric is not only able to detect wrong strings but also wrong output structures. For example, the prediction may be a list, although a dictionary was expected. All these cases are correctly handled by the ANLS* metric.

### 3.2 Formal definition of the ANLS* metric

In the following, the ground truth is denoted as $g$ and the prediction as $p$.
Note that the type of the ground truth $\texttt{type}(g)$ may differ from the type of the prediction $\texttt{type}(p)$ in case the GLLM returns incorrect results. For example, the GLLM may answer with a sentence although a list was expected. The idea of the metric is to generate a tree from the ground truth as well as a tree from the prediction and to compute a matching between both trees. Additionally, the metric is normalized to account for different lengths of the ground truth and the prediction. Overall, the ANLS* metric is defined as follows:

$$ $\displaystyle\text{ANLS*}(g,p)=\frac{s(g,p)}{l(g,p)}$ (1) $$

where $s$ is the score between the ground truth and the prediction and $l$ is the size of the trees $g$ and $p$ such that $\text{ANLS*}(g,p)\in[0,1]$. Additionally, it is worth noting that each prediction in this tree is given equal weight. This implies that leaf nodes of large sub-trees carry the same weight as leaf nodes that appear at the top level.

#### 3.2.1 Definition of the score s 𝑠 s italic_s

The score $s$ is defined recursively to measure the similarity between the ground truth and the prediction. Note that in order to distinguish between the *one of* semantic of a ground truth list used by the original ANLS metric, and the matching semantic implemented in the ANLSL metric, we introduced Tuples for the former and Lists for the latter. The score $s$ is defined as follows:

$$ $\displaystyle s(g,p)$ $\displaystyle=\begin{cases}1.0&\text{if }\texttt{type}(g)=\texttt{type}(p)= \text{None}\\ 1.0-\frac{\text{LD}(g,p)}{\max(|g|,|p|)}&\text{if }\texttt{type}(g)=\texttt{ type}(p)=\text{String}\text{ and }s(g,p)\geq\tau\\ s(g_{i},p)\text{ with }i=\operatorname*{argmax}_{i}(\text{ANLS*}(g_{i},p))& \text{if }\texttt{type}(g)=\text{Tuple}\\ \sum\limits_{(g_{i},p_{i})\in\psi(g,p)}s(g_{i},p_{i})&\text{if }\texttt{type}( g)=\texttt{type}(p)=\text{List}\\ \sum\limits_{k\in\texttt{keys}(p)}s(g_{k},p_{k})&\text{if }\texttt{type}(g)= \texttt{type}(p)=\text{Dict}\text{ and }k\in\text{keys}(p)\\ 0.0&\text{otherwise}\end{cases}$ (2) $$

with LD being the Levensthein distance and $\tau$ being the normalized Levensthein distance threshold which is set to $\tau=0.5$. $\psi$ is the Hungarian matching algorithm [9] performed according to the pairwise ANLS* of each ground truth and prediction element. This algorithm returns an optimal matching of elements between two lists w.r.t. a given score. The score for type mismatches (i.e., different subtrees) yields a score of $0.0$. The function $\texttt{keys}(x)$ returns all keys of a dictionary $x$, that are not None. It is important that $\texttt{keys}(x)$ ignores None values in order to penalize hallucinations correctly.

#### 3.2.2 Definition of the length l 𝑙 l italic_l

To normalize $s$, we define the length $l$ of each type as follows:

$$ $\displaystyle l(g,p)$ $\displaystyle=\begin{cases}1&\text{if }\texttt{type}(x)=\texttt{type}(p)=\text {None}\\ 1&\text{if }\texttt{type}(g)=\texttt{type}(p)=\text{String}\\ l(g_{i},p)\text{ with }i=\operatorname*{argmax}_{i}(\text{ANLS*}(g_{i},p))& \text{if }\texttt{type}(g)=\text{Tuple}\\ \sum\limits_{(g_{i},p_{i})\in\psi(g,p)}l(g_{i},p_{i})&\text{if }\texttt{type}( g)=\texttt{type}(p)=\text{List}\\ \qquad+\sum\limits_{g_{u}\notin\psi(g,p)}l_{t}(g_{u})\\ \qquad+\sum\limits_{p_{u}\notin\psi(g,p)}l_{t}(p_{u})\\ \sum\limits_{k\in\texttt{keys}(p)\cap\texttt{keys}(q)}l(g_{k},p_{k})&\text{if }\texttt{type}(g)=\texttt{type}(p)=\text{Dict}\\ \qquad+\sum\limits_{k\in\texttt{keys}(g)-\texttt{keys}(p)}l_{t}(g_{k})\\ \qquad+\sum\limits_{k\in\texttt{keys}(p)-\texttt{keys}(g)}l_{t}(p_{k})\\ \max(l_{t}(g),l_{t}(p))&\text{otherwise}\end{cases}$ (3) $$

As can be seen, the length is weighted for all type matches accordingly. Nevertheless, it is not guaranteed that the prediction produced the correct output structure. On the other hand, a partially correct structure should not get a sore of $0.0$. To this end, we match the subtree and penalize wrong types via another length function $l_{t}$. It can be seen that the maximum length is used between the ground truth and the prediction - $\max(l_{t}(g),l_{t}(p))$ – such that both, missing subtrees, as well as hallucinated subtrees, are penalized equally. The length function $l_{t}$ is defined as follows:

$$ $\displaystyle l_{t}(x)$ $\displaystyle=\begin{cases}1&\text{if }\texttt{type}(x)=\text{None}\\ 1&\text{if }\texttt{type}(x)=\text{String}\\ \max_{x_{i}\in x}l_{t}(x_{i})&\text{if }\texttt{type}(x)=\text{Tuple}\\ \sum\limits_{x_{i}\in x}l_{t}(x_{i})&\text{if }\texttt{type}(x)=\text{List}\\ \sum\limits_{k\in\texttt{keys}(x)}l_{t}(x_{k})&\text{if }\texttt{type}(x)= \text{Dict}\\ \end{cases}$ (4) $$

where $x$ is either a (sub)tree of the prediction $p$ or a (sub)tree of the ground truth $g$.

Using the ANLS* metric we will next showcase some examples to demonstrate the behavior of the metric. In a quantitative study, we will later show that ANLS* is a suitable metric for a wide variety of tasks.

## 4 Experimental Evaluation

In this section, we evaluate the performance of the ANLS* metric both qualitatively and quantitatively. The source code required to reproduce these results can be accessed at [https://github.com/deepopinion/anls_star_metric](https://github.com/deepopinion/anls_star_metric).

### 4.1 Examples

Different ANLS* scores for various ground truths and predictions are provided below, to offer the reader some insight into which predictions are considered as good and which are considered as bad. We also show some limitations of the proposed method. Note that tuples are interpreted as *one of* and lists are interpreted as *all of*.

**Table 1: ANLS* scores for different predictions and ground truth types.**
| Id | Description | Ground Truth | Prediction | ANLS* |
| --- | --- | --- | --- | --- |
| 1 | Correct String | Hello World | Hello World | 1.0 |
| 2 | Typo | Hello World | Hello Wolrd | 0.82 |
| 3 | Incorrect String | Hello World | How are you? | 0.0 |
| 4 | Hallucination | None | Hello World! | 0.0 |
| 5 | One of n | tuple(Hello, World) | Hello | 1.0 |
| 6 | Typo in one of n | tuple(Hello, World) | Wolrd | 0.6 |
| 7 | Expected String | Hello World | list(Hello, World) | 0.0 |
| 8 | Correct List | list(Hello, World) | list(World, Hello) | 1.0 |
| 9 | Missing Element | list(Hello, World) | list(Hello) | 0.5 |
| 10 | Correct Dict | {a:Hello, b:World} | {b:World, a:Hello} | 1.0 |
| 11 | Missig Key | {a:Hello, b:World} | {a:Hello} | 0.5 |
| 12 | Hallucinated Key | {a:Hello, b:World} | {b:World, a:Hello, c:Great} | 0.67 |
| 13 | Complex Object | {a:Hello, b:list(W,r,l,d)} | {a:Hello, b:list(w,r,d)} | 0.8 |

**Table 2: ANLS* scores for edge cases.**
| Id | Description | Ground Truth | Prediction | ANLS* |
| --- | --- | --- | --- | --- |
| 14 | list casted implicitly to tuple | list(Hello, World) | Hello | 1.0 |
| 15 | Comparison of numbers | 0.2 | 0.199999999 | 0.0 |
| 16 | Incorrect Format | 31.12.2023 | 31.Dec 2023 | 0.58 |
| 17 | Unanswerable Question - Incorrect Answer | Yesterday | Last Week | 0.0 |
| 18 | Unanswerable Question - No Answer | Yesterday | None | 0.0 |

Several cases for good and bad predictions including type mismatches are shown in [Table 1](https://arxiv.org/html/2402.03848v3#S4.T1). Additionally, we added some edge cases in [Table 2](https://arxiv.org/html/2402.03848v3#S4.T2) that may seem counter-intuitive at first, but they are required in order to keep the metric consistent with the previously defined ANLS and ANLSL metrics.

The first edge case #14 shown in [Table 2](https://arxiv.org/html/2402.03848v3#S4.T2) (list automatically casted to a tuple) is implemented to ensure compatibility with common datasets where possible answers are returned as lists, while the actual answer is a single string. According to the proposed semantics, all possible answers should be tuples. However, to ensure the reproducibility of experiments with classical QA datasets, we implemented this implicit casting in cases where the ground truth is a list and the prediction is a string. In case 15, it is evident that numbers are not interpreted as numbers, but a string comparison is performed instead. Case 16 illustrates that different formats may produce a high error, even though the semantics are the same. Lastly, cases 17 and 18 demonstrate that completely incorrect answers are weighted equally to missing answers.

### 4.2 Experimental Evaluation

In this subsection, the quantitative evaluation of the ANLS* metric on many different datasets and different GLLMs is shown. More precisely, we evaluated two QA datasets (DocVQA [11], MPDocVQA [21]) and five information extraction datasets (Kleister Charity [15], Kleister NDA [15], SROIE [6], VRDU Ad Buy [27], VRDU Registration[27]). The following model versions were used for the evaluation: gpt-3.5-turbo-16k (Version gpt-3.5-turbo-16k-0613), gpt-4-turbo (Version gpt-4-1106-preview) [2], gpt-4-vision (Version gpt-4-vision-preview-1106), gemini-pro (Version 1.0) [17], mistral-large (Feb. 2024) [18] as well as claude-3 (Version claude-3-opus) [16].

We used LangChain [1] for the implementation. Whenever a request to a provider failed (e.g. network timeouts etc.), we send the same request with a sleep time of 10 seconds again. After 5 retries we considered the request as failed resulting in ANLS* of 0.0. We used the following prompts to query each model:

##### QA prompt

You are a world-class question answering system.  You are given a document and a question. You must answer the question based on the document.  Precisely answer the question without any additional text.  Its very important to NOT write full sentences!  Note: Ensure that the answer is precisely contained in the original document.  Here is the document:  {document}  Here is the question:  {question}

##### Information extraction prompt

You are a document information extraction system.  You are given a document and a json with keys that must be extracted from the document.  Here is the document:  {document}  {format_instructions}     Format extractions are automatically generated by LangChain according to the given dataset and keys that must be extracted. For representing the document itself, different prompting methods were evaluated (Simple, LATIN, SFT). More details can be found in the provided source code. For vision based models we excluded the document and added one user message per page directly including the corresponding image without executing any OCR.

Note that special prompting techniques were required for mistral-large as well as claude-3 in order to get decent values. We refer to the source code for more details. The results are shown in [Table 3](https://arxiv.org/html/2402.03848v3#S4.T3).

**Table 3: ANLS* score for different GLLMs and Datasets. No document prompting method is required for vision-based models. Therefore Latin Prompting and SFT is not executed for those.**
| Dataset | Method | gpt-3.5-turbo-16k | gpt-4-turbo | gpt-4-vision | gemini-pro | mistral-large | claude-3 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DocVQA | Simple | 0.586 | 0.607 | 0.759 | 0.586 | 0.445 | 0.768 |
|  | Latin Prompting | 0.659 | 0.699 | - | 0.676 | 0.447 | 0.762 |
|  | SFT (Ours) | 0.809 | 0.790 | - | 0.741 | 0.648 | 0.831 |
| MPDocVQA | Simple | 0.517 | 0.635 | 0.708 | 0.603 | 0.364 | 0.636 |
|  | Latin Prompting | 0.499 | 0.739 | - | 0.502 | 0.335 | 0.438 |
|  | SFT (Ours) | 0.734 | 0.781 | - | 0.616 | 0.476 | 0.575 |
| Kleister Charity | Simple | 0.490 | 0.743 | 0.751 | 0.583 | 0.652 | 0.800 |
|  | Latin Prompting | 0.442 | 0.735 | - | 0.478 | 0.576 | 0.787 |
|  | SFT (Ours) | 0.476 | 0.763 | - | 0.633 | 0.657 | 0.786 |
| Kleister NDA | Simple | 0.343 | 0.695 | 0.664 | 0.623 | 0.637 | 0.673 |
|  | Latin Prompting | 0.434 | 0.705 | - | 0.599 | 0.624 | 0.67 |
|  | SFT (Ours) | 0.355 | 0.703 | - | 0.552 | 0.641 | 0.677 |
| SROIE | Simple | 0.874 | 0.835 | 0.834 | 0.263 | 0.855 | 0.933 |
|  | Latin Prompting | 0.849 | 0.851 | - | 0.371 | 0.863 | 0.926 |
|  | SFT (Ours) | 0.893 | 0.873 | - | 0.288 | 0.905 | 0.949 |
| VRDU AD Buy | Simple | 0.402 | 0.553 | 0.640 | 0.510 | 0.386 | 0.577 |
|  | Latin Prompting | 0.389 | 0.586 | - | 0.556 | 0.435 | 0.608 |
|  | SFT (Ours) | 0.661 | 0.770 | - | 0.685 | 0.594 | 0.633 |
| VRDU Registration | Simple | 0.659 | 0.676 | 0.665 | 0.699 | 0.579 | 0.685 |
|  | Latin Prompting | 0.693 | 0.673 | - | 0.740 | 0.587 | 0.715 |
|  | SFT (Ours) | 0.723 | 0.711 | - | 0.720 | 0.639 | 0.705 |

##### GLLM Comparison

First of all, it can be seen that the only model that competes against gpt-4-turbo is claude-3. Both models are good in both, VQA as well as IE tasks. So its not clear yet when to select gpt-4-turbo or claude-3. Nevertheless, it can be seen that gemini-pro, mistral-large as well as gpt-3.5-turbo-16k are quite behind those two models and gpt-4-turbo or claude-3 should be selected for document processing tasks. We believe that Google as well as Mistral will release new competitive versions in the future.

##### Different Prompting Methods

Table [Table 3](https://arxiv.org/html/2402.03848v3#S4.T3) shows the result for three different prompting methods. The highest scores of 5 out of 7 datasets were achieved with our SFT method. Only for Kleister Charity and Kleister NDA this was not the case. Results for KleisterNDA are very close ($0.703$ vs. $0.705$). For Kleister Charity we found that documents contain mainly text and almost no positional encoding which may describe why SFT and LATIN did not improve simple prompting. Nevertheless, documents usually contain 2D structures and not purely text which shows the importance of specialized prompt formatting techniques such as SFT.

##### GLLMs with Vision Capabilities

Prompting techniques are mainly required as those models only support text input. Nevertheless, some models exist that support vision capabilities. Although the gpt-4-vision model reaches decent scores, it is still behind our SFT solution which exploits an OCR scanner. In all cases gpt-4-turbo + SFT outperformed gpt-4-vision. This is a strong indicator that vision models are not yet competitive against specialized OCR scanners when combined with advanced prompting techniques.

##### Comparison with DocLLM

Wang et al. [25] developed and trained a special generative model for documents with 7B parameters. They report 0.634 on DocVQA and 0.499 zero-shot scores on Kleister Charity. Those scores are quite behind our gpt-4-turbo + SFT solution with 0.79 on DocVQA and 0.763 on Kleister Charity. This shows that smaller specialized models are not yet competitive against large purely text-based models that exploit specialized document prompting techniques.

##### Open-source Models

We also made tests with mixtral-8x7b, but found that those models are still far behind closed-source models. We, therefore, decided to not include those models in the final evaluation and will report additional results in a future or updated publication.

## 5 Conclusion & Discussion

In this paper, we introduce a novel metric called ANLS*, which serves as a plug-in replacement for existing ANLS metrics. This metric is not only applicable for traditional GLLM tasks such as QA, but also for information extraction tasks, and even for more complex outputs. We demonstrate that ANLS* is a versatile metric for a broad range of tasks. We evaluate the ANLS* metric using three different GLLMs on seven different datasets. We also demonstrate that more advanced methods such as SFT outperform prompting techniques, such as LATIN. We found that claude-3 is competitive against gpt-4-turbo, but all others are still behind those two models. For DocLLM we beliefe that this specially trained model is still too small with 7B parameters to be competitive against larger pure text-based models. Unfortunately, it is not available at the time of writing such that combinations of prompting techniques with DocLLM can not be tested yet.

We posit that ANLS* is a suitable metric for the evaluation of generative models and should be adopted for future use. We also claim that the ANLS* metric is suitable for discriminative models, allowing for a comparison of generative and discriminative models using a single metric. We hope that the ANLS* metric will be adopted by the community in the future.

## References

- [1]
Langchain.
[https://github.com/langchain-ai/langchain](https://github.com/langchain-ai/langchain).
Accessed: 31-01-2024.
- Achiam et al. [2023]
Josh Achiam, Steven Adler, Sandhini Agarwal, Lama Ahmad, Ilge Akkaya,
Florencia Leoni Aleman, Diogo Almeida, Janko Altenschmidt, Sam Altman,
Shyamal Anadkat, et al.
Gpt-4 technical report.
*arXiv preprint arXiv:2303.08774*, 2023.
- Biten et al. [2019]
Ali Furkan Biten, Ruben Tito, Andres Mafla, Lluis Gomez, Marçal Rusinol,
Ernest Valveny, CV Jawahar, and Dimosthenis Karatzas.
Scene text visual question answering.
In *Proceedings of the IEEE/CVF international conference on
computer vision*, pages 4291–4301, 2019.
- Devlin et al. [2019]
Jacob Devlin, Ming-Wei Chang, Kenton Lee, and Kristina Toutanova.
BERT: Pre-training of deep bidirectional transformers for language
understanding.
In *Proceedings of the 2019 Conference of the North American
Chapter of the Association for Computational Linguistics: Human Language
Technologies*, pages 4171–4186, Minneapolis, Minnesota, June 2019.
Association for Computational Linguistics.
- Huang et al. [2022]
Yupan Huang, Tengchao Lv, Lei Cui, Yutong Lu, and Furu Wei.
Layoutlmv3: Pre-training for document ai with unified text and image
masking.
In *Proceedings of the 30th ACM International Conference on
Multimedia*, pages 4083–4091, 2022.
- Huang et al. [2019]
Zheng Huang, Kai Chen, Jianhua He, Xiang Bai, Dimosthenis Karatzas, Shijian Lu,
and CV Jawahar.
Icdar2019 competition on scanned receipt ocr and information
extraction.
In *2019 International Conference on Document Analysis and
Recognition (ICDAR)*, pages 1516–1520. IEEE, 2019.
- Kaplan et al. [2020]
Jared Kaplan, Sam McCandlish, Tom Henighan, Tom B Brown, Benjamin Chess, Rewon
Child, Scott Gray, Alec Radford, Jeffrey Wu, and Dario Amodei.
Scaling laws for neural language models.
*arXiv preprint arXiv:2001.08361*, 2020.
- Kim et al. [2022]
Geewook Kim, Teakgyu Hong, Moonbin Yim, JeongYeon Nam, Jinyoung Park, Jinyeong
Yim, Wonseok Hwang, Sangdoo Yun, Dongyoon Han, and Seunghyun Park.
Ocr-free document understanding transformer.
In *European Conference on Computer Vision*, pages 498–517.
Springer, 2022.
- Kuhn [1955]
Harold W Kuhn.
The hungarian method for the assignment problem.
*Naval research logistics quarterly*, 2(1-2):83–97, 1955.
- Levenshtein et al. [1966]
Vladimir I Levenshtein et al.
Binary codes capable of correcting deletions, insertions, and
reversals.
In *Soviet physics doklady*, volume 10, pages 707–710. Soviet
Union, 1966.
- Mathew et al. [2021]
Minesh Mathew, Dimosthenis Karatzas, and CV Jawahar.
Docvqa: A dataset for vqa on document images.
In *Proceedings of the IEEE/CVF winter conference on
applications of computer vision*, pages 2200–2209, 2021.
- Peer et al. [2022a]
David Peer, Bart Keulen, Sebastian Stabinger, Justus Piater, and Antonio
Rodriguez-Sanchez.
Improving the trainability of deep neural networks through layerwise
batch-entropy regularization.
*Transactions on Machine Learning Research*, 2022a.
URL [https://openreview.net/forum?id=LJohl5DnZf](https://openreview.net/forum?id=LJohl5DnZf).
- Peer et al. [2022b]
David Peer, Sebastian Stabinger, Stefan Engl, and Antonio
Rodríguez-Sánchez.
Greedy-layer pruning: Speeding up transformer models for natural
language processing.
*Pattern Recognition Letters*, 157:76–82,
2022b.
- Šimsa et al. [2023]
Štěpán Šimsa, Milan Šulc, Michal
Uřičář, Yash Patel, Ahmed Hamdi, Matěj
Kocián, Matyáš Skalickỳ, Jiří Matas, Antoine
Doucet, Mickaël Coustaty, et al.
Docile benchmark for document information localization and
extraction.
*arXiv preprint arXiv:2302.05658*, 2023.
- Stanisławek et al. [2021]
Tomasz Stanisławek, Filip Graliński, Anna Wróblewska, Dawid
Lipiński, Agnieszka Kaliska, Paulina Rosalska, Bartosz Topolski, and
Przemysław Biecek.
Kleister: key information extraction datasets involving long
documents with complex layouts.
In *International Conference on Document Analysis and
Recognition*, pages 564–579. Springer, 2021.
- Team [a]
Claude AI Team.
Claude-3.
[https://www.anthropic.com/news/claude-3-family](https://www.anthropic.com/news/claude-3-family), a.
Accessed: 20-03-2024.
- Team et al. [2023]
Gemini Team, Rohan Anil, Sebastian Borgeaud, Yonghui Wu, Jean-Baptiste Alayrac,
Jiahui Yu, Radu Soricut, Johan Schalkwyk, Andrew M Dai, Anja Hauth, et al.
Gemini: a family of highly capable multimodal models.
*arXiv preprint arXiv:2312.11805*, 2023.
- Team [b]
Mistral AI Team.
Mistral large.
[https://mistral.ai/news/mistral-large/](https://mistral.ai/news/mistral-large/), b.
Accessed: 27-02-2024.
- Tian et al. [2023]
Katherine Tian, Eric Mitchell, Allan Zhou, Archit Sharma, Rafael Rafailov,
Huaxiu Yao, Chelsea Finn, and Christopher D Manning.
Just ask for calibration: Strategies for eliciting calibrated
confidence scores from language models fine-tuned with human feedback.
*arXiv preprint arXiv:2305.14975*, 2023.
- Tito et al. [2021]
Rubèn Tito, Dimosthenis Karatzas, and Ernest Valveny.
Document collection visual question answering.
In *Document Analysis and Recognition–ICDAR 2021: 16th
International Conference, Lausanne, Switzerland, September 5–10, 2021,
Proceedings, Part II 16*, pages 778–792. Springer, 2021.
- Tito et al. [2023]
Rubèn Tito, Dimosthenis Karatzas, and Ernest Valveny.
Hierarchical multimodal transformers for multipage docvqa.
*Pattern Recognition*, 144:109834, 2023.
- Van Landeghem et al. [2023a]
Jordy Van Landeghem, Rubèn Tito, Łukasz Borchmann, Michał Pietruszka,
Pawel Joziak, Rafal Powalski, Dawid Jurkiewicz, Mickaël Coustaty,
Bertrand Anckaert, Ernest Valveny, et al.
Document understanding dataset and evaluation (dude).
In *Proceedings of the IEEE/CVF International Conference on
Computer Vision*, pages 19528–19540, 2023a.
- Van Landeghem et al. [2023b]
Jordy Van Landeghem, Rubèn Tito, Łukasz Borchmann, Michał Pietruszka,
Pawel Joziak, Rafal Powalski, Dawid Jurkiewicz, Mickaël Coustaty,
Bertrand Anckaert, Ernest Valveny, et al.
Document understanding dataset and evaluation (dude).
In *Proceedings of the IEEE/CVF International Conference on
Computer Vision*, pages 19528–19540, 2023b.
- Vedantam et al. [2015]
Ramakrishna Vedantam, C Lawrence Zitnick, and Devi Parikh.
Cider: Consensus-based image description evaluation.
In *Proceedings of the IEEE conference on computer vision and
pattern recognition*, pages 4566–4575, 2015.
- Wang et al. [2023a]
Dongsheng Wang, Natraj Raman, Mathieu Sibue, Zhiqiang Ma, Petr Babkin, Simerjot
Kaur, Yulong Pei, Armineh Nourbakhsh, and Xiaomo Liu.
Docllm: A layout-aware generative language model for multimodal
document understanding.
*arXiv preprint arXiv:2401.00908*, 2023a.
- Wang et al. [2023b]
Wenjin Wang, Yunhao Li, Yixin Ou, and Yin Zhang.
Layout and task aware instruction prompt for zero-shot document image
question answering, 2023b.
- Wang et al. [2023c]
Zilong Wang, Yichao Zhou, Wei Wei, Chen-Yu Lee, and Sandeep Tata.
Vrdu: A benchmark for visually-rich document understanding.
In *Proceedings of the 29th ACM SIGKDD Conference on Knowledge
Discovery and Data Mining*, pages 5184–5193, 2023c.
- Xu et al. [2021]
Yang Xu, Yiheng Xu, Tengchao Lv, Lei Cui, Furu Wei, Guoxin Wang, Yijuan Lu,
Dinei Florencio, Cha Zhang, Wanxiang Che, Min Zhang, and Lidong Zhou.
LayoutLMv2: Multi-modal pre-training for visually-rich document
understanding.
pages 2579–2591, Online, August 2021. Association for Computational
Linguistics.
- Xu et al. [2020]
Yiheng Xu, Minghao Li, Lei Cui, Shaohan Huang, Furu Wei, and Ming Zhou.
Layoutlm: Pre-training of text and layout for document image
understanding.
In *Proceedings of the 26th ACM SIGKDD International Conference
on Knowledge Discovery & Data Mining*, pages 1192–1200, 2020.
- Ye et al. [2023]
Jiabo Ye, Anwen Hu, Haiyang Xu, Qinghao Ye, Ming Yan, Yuhao Dan, Chenlin Zhao,
Guohai Xu, Chenliang Li, Junfeng Tian, et al.
mplug-docowl: Modularized multimodal large language model for
document understanding.
*arXiv preprint arXiv:2307.02499*, 2023.