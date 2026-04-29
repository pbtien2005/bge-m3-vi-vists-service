---
tags:
- sentence-transformers
- sentence-similarity
- feature-extraction
- generated_from_trainer
- dataset_size:23781
- loss:CosineSimilarityLoss
base_model: BAAI/bge-m3
widget:
- source_sentence: Một cậu bé đang mặc tất cả màu đen và đang trượt xuống một thổi
    lên trượt vàng
  sentences:
  - Một cô gái mặc tất cả màu đen và đang trượt xuống một thổi lên trượt vàng
  - câu trả lời ngắn gọn là tiến hóa không thể tạo ra nến ở con người.
  - Tất cả là về sự gắn kết.
- source_sentence: Một người phụ nữ đặt hai quả trứng vào một bình nước
  sentences:
  - 'Mâu thuẫn trên giàn khoan dầu: Bắc Kinh không gửi quân đội'
  - Hai đứa trẻ đang nhảy vọt trên những quả bóng màu sắc
  - Một người phụ nữ đang đun sôi trứng
- source_sentence: Một cựu chiến binh đang cho thấy những điều khác nhau từ một cuộc
    chiến tranh cho một số người
  sentences:
  - Một người đàn ông nhỏ đang ngồi trong một cửa hàng phụ kiện quân sự
  - những người đồng tính và những hành vi " hiện đại " khác bị từ chối, bởi vì họ
    là những người có tâm hồn.
  - Violin đang được chơi bởi một cô gái nhỏ trên một bãi biển
- source_sentence: Một cô gái đang nhảy xuống một tảng đá và một cô gái khác đang
    đứng trên đó.
  sentences:
  - không tiết kiệm và không thỏa hiệp trong kỷ luật hoặc phán xét;
  - Một người phụ nữ đang đi xe đạp.
  - Một cô gái đang nhảy xuống một tảng đá và một cô gái khác đang đứng trên đó.
- source_sentence: Trẻ em của một gia đình đang chơi và chờ đợi
  sentences:
  - không có đa số đủ điều kiện trong quốc hội này để quay lại Điều 272.
  - 100 người ủng hộ Palestine tìm cách vào Israel tại Allenby
  - Ba đứa trẻ châu Á đang nhảy múa và một người đàn ông nghiêm túc đang nhìn
pipeline_tag: sentence-similarity
library_name: sentence-transformers
metrics:
- pearson_cosine
- spearman_cosine
model-index:
- name: BAAI/bge-m3
  results:
  - task:
      type: semantic-similarity
      name: Semantic Similarity
    dataset:
      name: vi sts test
      type: vi-sts-test
    metrics:
    - type: pearson_cosine
      value: 0.9545567179350732
      name: Pearson Cosine
    - type: spearman_cosine
      value: 0.9526457038738844
      name: Spearman Cosine
---

# BAAI/bge-m3

This is a [sentence-transformers](https://www.SBERT.net) model finetuned from [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3). It maps sentences & paragraphs to a 1024-dimensional dense vector space and can be used for retrieval.

## Model Details

### Model Description
- **Model Type:** Sentence Transformer
- **Base model:** [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3) <!-- at revision 5617a9f61b028005a4858fdac845db406aefb181 -->
- **Maximum Sequence Length:** 512 tokens
- **Output Dimensionality:** 1024 dimensions
- **Similarity Function:** Cosine Similarity
- **Supported Modality:** Text
<!-- - **Training Dataset:** Unknown -->
<!-- - **Language:** Unknown -->
<!-- - **License:** Unknown -->

### Model Sources

- **Documentation:** [Sentence Transformers Documentation](https://sbert.net)
- **Repository:** [Sentence Transformers on GitHub](https://github.com/huggingface/sentence-transformers)
- **Hugging Face:** [Sentence Transformers on Hugging Face](https://huggingface.co/models?library=sentence-transformers)

### Full Model Architecture

```
SentenceTransformer(
  (0): Transformer({'transformer_task': 'feature-extraction', 'modality_config': {'text': {'method': 'forward', 'method_output_name': 'last_hidden_state'}}, 'module_output_name': 'token_embeddings', 'architecture': 'XLMRobertaModel'})
  (1): Pooling({'embedding_dimension': 1024, 'pooling_mode': 'cls', 'include_prompt': True})
  (2): Normalize({})
)
```

## Usage

### Direct Usage (Sentence Transformers)

First install the Sentence Transformers library:

```bash
pip install -U sentence-transformers
```
Then you can load this model and run inference.
```python
from sentence_transformers import SentenceTransformer

# Download from the 🤗 Hub
model = SentenceTransformer("sentence_transformers_model_id")
# Run inference
sentences = [
    'Trẻ em của một gia đình đang chơi và chờ đợi',
    'Ba đứa trẻ châu Á đang nhảy múa và một người đàn ông nghiêm túc đang nhìn',
    '100 người ủng hộ Palestine tìm cách vào Israel tại Allenby',
]
embeddings = model.encode(sentences)
print(embeddings.shape)
# [3, 1024]

# Get the similarity scores for the embeddings
similarities = model.similarity(embeddings, embeddings)
print(similarities)
# tensor([[1.0000, 0.4454, 0.1098],
#         [0.4454, 1.0000, 0.1127],
#         [0.1098, 0.1127, 1.0000]])
```
<!--
### Direct Usage (Transformers)

<details><summary>Click to see the direct usage in Transformers</summary>

</details>
-->

<!--
### Downstream Usage (Sentence Transformers)

You can finetune this model on your own dataset.

<details><summary>Click to expand</summary>

</details>
-->

<!--
### Out-of-Scope Use

*List how the model may foreseeably be misused and address what users ought not to do with the model.*
-->

## Evaluation

### Metrics

#### Semantic Similarity

* Dataset: `vi-sts-test`
* Evaluated with [<code>EmbeddingSimilarityEvaluator</code>](https://sbert.net/docs/package_reference/sentence_transformer/evaluation.html#sentence_transformers.sentence_transformer.evaluation.EmbeddingSimilarityEvaluator)

| Metric              | Value      |
|:--------------------|:-----------|
| pearson_cosine      | 0.9546     |
| **spearman_cosine** | **0.9526** |

<!--
## Bias, Risks and Limitations

*What are the known or foreseeable issues stemming from this model? You could also flag here known failure cases or weaknesses of the model.*
-->

<!--
### Recommendations

*What are recommendations with respect to the foreseeable issues? For example, filtering explicit content.*
-->

## Training Details

### Training Dataset

#### Unnamed Dataset

* Size: 23,781 training samples
* Columns: <code>sentence_0</code>, <code>sentence_1</code>, and <code>label</code>
* Approximate statistics based on the first 1000 samples:
  |         | sentence_0                                                                        | sentence_1                                                                        | label                                                          |
  |:--------|:----------------------------------------------------------------------------------|:----------------------------------------------------------------------------------|:---------------------------------------------------------------|
  | type    | string                                                                            | string                                                                            | float                                                          |
  | details | <ul><li>min: 4 tokens</li><li>mean: 17.2 tokens</li><li>max: 106 tokens</li></ul> | <ul><li>min: 4 tokens</li><li>mean: 16.24 tokens</li><li>max: 58 tokens</li></ul> | <ul><li>min: 0.0</li><li>mean: 0.61</li><li>max: 1.0</li></ul> |
* Samples:
  | sentence_0                                                                                           | sentence_1                                                                     | label                            |
  |:-----------------------------------------------------------------------------------------------------|:-------------------------------------------------------------------------------|:---------------------------------|
  | <code>một người đàn ông chơi đàn guitar.</code>                                                      | <code>một người đàn ông chơi đàn piano.</code>                                 | <code>0.27999999999999997</code> |
  | <code>Đại sứ quán Vatican ở Syria bị tấn công bởi súng cối</code>                                    | <code>Đại sứ quán Vatican ở Syria bị tấn công; không có người bị thương</code> | <code>0.72</code>                |
  | <code>Gore Vidal chết ở tuổi 86: Nhà văn huyền thoại, nhà viết kịch, và chính trị gia qua đời</code> | <code>Gore Vidal, tác giả nổi tiếng, nhà viết kịch, qua đời ở tuổi 86</code>   | <code>0.8</code>                 |
* Loss: [<code>CosineSimilarityLoss</code>](https://sbert.net/docs/package_reference/sentence_transformer/losses.html#cosinesimilarityloss) with these parameters:
  ```json
  {
      "loss_fct": "torch.nn.modules.loss.MSELoss",
      "cos_score_transformation": "torch.nn.modules.linear.Identity"
  }
  ```

### Training Hyperparameters
#### Non-Default Hyperparameters

- `fp16`: True
- `multi_dataset_batch_sampler`: round_robin

#### All Hyperparameters
<details><summary>Click to expand</summary>

- `per_device_train_batch_size`: 8
- `num_train_epochs`: 3
- `max_steps`: -1
- `learning_rate`: 5e-05
- `lr_scheduler_type`: linear
- `lr_scheduler_kwargs`: None
- `warmup_steps`: 0
- `optim`: adamw_torch
- `optim_args`: None
- `weight_decay`: 0.0
- `adam_beta1`: 0.9
- `adam_beta2`: 0.999
- `adam_epsilon`: 1e-08
- `optim_target_modules`: None
- `gradient_accumulation_steps`: 1
- `average_tokens_across_devices`: True
- `max_grad_norm`: 1
- `label_smoothing_factor`: 0.0
- `bf16`: False
- `fp16`: True
- `bf16_full_eval`: False
- `fp16_full_eval`: False
- `tf32`: None
- `gradient_checkpointing`: False
- `gradient_checkpointing_kwargs`: None
- `torch_compile`: False
- `torch_compile_backend`: None
- `torch_compile_mode`: None
- `use_liger_kernel`: False
- `liger_kernel_config`: None
- `use_cache`: False
- `neftune_noise_alpha`: None
- `torch_empty_cache_steps`: None
- `auto_find_batch_size`: False
- `log_on_each_node`: True
- `logging_nan_inf_filter`: True
- `include_num_input_tokens_seen`: no
- `log_level`: passive
- `log_level_replica`: warning
- `disable_tqdm`: False
- `project`: huggingface
- `trackio_space_id`: trackio
- `per_device_eval_batch_size`: 8
- `prediction_loss_only`: True
- `eval_on_start`: False
- `eval_do_concat_batches`: True
- `eval_use_gather_object`: False
- `eval_accumulation_steps`: None
- `include_for_metrics`: []
- `batch_eval_metrics`: False
- `save_only_model`: False
- `save_on_each_node`: False
- `enable_jit_checkpoint`: False
- `push_to_hub`: False
- `hub_private_repo`: None
- `hub_model_id`: None
- `hub_strategy`: every_save
- `hub_always_push`: False
- `hub_revision`: None
- `load_best_model_at_end`: False
- `ignore_data_skip`: False
- `restore_callback_states_from_checkpoint`: False
- `full_determinism`: False
- `seed`: 42
- `data_seed`: None
- `use_cpu`: False
- `accelerator_config`: {'split_batches': False, 'dispatch_batches': None, 'even_batches': True, 'use_seedable_sampler': True, 'non_blocking': False, 'gradient_accumulation_kwargs': None}
- `parallelism_config`: None
- `dataloader_drop_last`: False
- `dataloader_num_workers`: 0
- `dataloader_pin_memory`: True
- `dataloader_persistent_workers`: False
- `dataloader_prefetch_factor`: None
- `remove_unused_columns`: True
- `label_names`: None
- `train_sampling_strategy`: random
- `length_column_name`: length
- `ddp_find_unused_parameters`: None
- `ddp_bucket_cap_mb`: None
- `ddp_broadcast_buffers`: False
- `ddp_backend`: None
- `ddp_timeout`: 1800
- `fsdp`: []
- `fsdp_config`: {'min_num_params': 0, 'xla': False, 'xla_fsdp_v2': False, 'xla_fsdp_grad_ckpt': False}
- `deepspeed`: None
- `debug`: []
- `skip_memory_metrics`: True
- `do_predict`: False
- `resume_from_checkpoint`: None
- `warmup_ratio`: None
- `local_rank`: -1
- `prompts`: None
- `batch_sampler`: batch_sampler
- `multi_dataset_batch_sampler`: round_robin
- `router_mapping`: {}
- `learning_rate_mapping`: {}

</details>

### Training Logs
| Epoch  | Step | Training Loss | vi-sts-test_spearman_cosine |
|:------:|:----:|:-------------:|:---------------------------:|
| 0.1682 | 500  | 0.0292        | 0.8617                      |
| 0.3364 | 1000 | 0.0223        | 0.8727                      |
| 0.5045 | 1500 | 0.0226        | 0.8830                      |
| 0.6727 | 2000 | 0.0211        | 0.8975                      |
| 0.8409 | 2500 | 0.0206        | 0.9049                      |
| 1.0    | 2973 | -             | 0.9144                      |
| 1.0091 | 3000 | 0.0182        | 0.9197                      |
| 1.1773 | 3500 | 0.0112        | 0.9271                      |
| 1.3454 | 4000 | 0.0109        | 0.9320                      |
| 1.5136 | 4500 | 0.0119        | 0.9323                      |
| 1.6818 | 5000 | 0.0112        | 0.9380                      |
| 1.8500 | 5500 | 0.0107        | 0.9373                      |
| 2.0    | 5946 | -             | 0.9441                      |
| 2.0182 | 6000 | 0.0103        | 0.9452                      |
| 2.1863 | 6500 | 0.0061        | 0.9461                      |
| 2.3545 | 7000 | 0.0061        | 0.9485                      |
| 2.5227 | 7500 | 0.0062        | 0.9496                      |
| 2.6909 | 8000 | 0.0058        | 0.9513                      |
| 2.8591 | 8500 | 0.0057        | 0.9525                      |
| 3.0    | 8919 | -             | 0.9526                      |


### Training Time
- **Training**: 57.8 minutes

### Framework Versions
- Python: 3.13.12
- Sentence Transformers: 5.4.1
- Transformers: 5.5.4
- PyTorch: 2.7.1+cu118
- Accelerate: 1.13.0
- Datasets: 4.8.4
- Tokenizers: 0.22.2

## Citation

### BibTeX

#### Sentence Transformers
```bibtex
@inproceedings{reimers-2019-sentence-bert,
    title = "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks",
    author = "Reimers, Nils and Gurevych, Iryna",
    booktitle = "Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing",
    month = "11",
    year = "2019",
    publisher = "Association for Computational Linguistics",
    url = "https://arxiv.org/abs/1908.10084",
}
```

<!--
## Glossary

*Clearly define terms in order to be accessible across audiences.*
-->

<!--
## Model Card Authors

*Lists the people who create the model card, providing recognition and accountability for the detailed work that goes into its construction.*
-->

<!--
## Model Card Contact

*Provides a way for people who have updates to the Model Card, suggestions, or questions, to contact the Model Card authors.*
-->