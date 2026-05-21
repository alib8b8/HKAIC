# HKAIC DeepSeek微调方案

---

## 📋 目录

1. [方案概述](#方案概述)
2. [模型选择](#模型选择)
3. [数据准备](#数据准备)
4. [微调流程](#微调流程)
5. [部署方案](#部署方案)
6. [性能评估](#性能评估)
7. [持续优化](#持续优化)

---

## 🎯 方案概述

### 目标

基于DeepSeek开源大模型，为HKAIC打造专属的**AI调参助手**，实现：

- 🤖 自然语言理解无人机调参需求
- 🎯 精准PID参数推荐
- 📚 专业级调参知识问答
- 🔧 多种飞控平台适配

### 核心优势

- **开源可控**：基于DeepSeek MIT协议开源模型
- **成本可控**：LoRA微调，训练成本降低90%
- **性能优异**：7B模型即可达到专业调参水平
- **快速迭代**：支持持续学习和优化

---

## 🧠 模型选择

### 推荐模型对比

| 模型 | 参数量 | 显存需求 | 推理速度 | 调参能力 | 部署难度 |
|------|--------|---------|---------|---------|---------|
| **DeepSeek-R1-Distill-Qwen-7B** ⭐ | 7B | 16GB | 快 | ★★★★★ | 简单 |
| DeepSeek-V3-7B | 7B | 20GB | 快 | ★★★★☆ | 简单 |
| DeepSeek-R1-Distill-Llama-8B | 8B | 18GB | 快 | ★★★★★ | 简单 |
| DeepSeek-67B | 67B | 140GB | 中 | ★★★★★ | 复杂 |
| DeepSeek-V3-671B | 671B | 多卡 | 慢 | ★★★★★ | 专业 |

### 最终选择：DeepSeek-R1-Distill-Qwen-7B

**理由：**
1. ✅ MoE架构优化，仅7B参数即可达到70B效果
2. ✅ MIT协议，完全开源可商用
3. ✅ 推理能力强，特别适合调参场景
4. ✅ 单卡RTX 4090即可部署
5. ✅ 社区活跃，文档完善

---

## 📊 数据准备

### 数据来源

#### 1. 公开数据集

- PX4官方调参文档
- Betaflight官方Wiki
- 开源调参社区数据
- 学术论文中的调参案例

#### 2. 用户数据（脱敏后）

- 匿名化调参对话记录
- 飞行日志参数配置
- 用户反馈数据

#### 3. 专家知识

- 专业飞手调参经验
- 行业专家知识库
- 官方推荐配置

### 数据格式

```json
{
  "conversations": [
    {
      "role": "system",
      "content": "你是一个专业的无人机调参助手，熟悉PX4和Betaflight飞控系统。"
    },
    {
      "role": "user", 
      "content": "我的穿越机在高速飞行时有点抖动，怎么调整？"
    },
    {
      "role": "assistant",
      "content": "根据您描述的'高速飞行抖动'问题，这是典型的P值过高或D值不足导致的振荡。建议：\n\n1. Roll P值降低2-3个单位\n2. Roll D值增加3-5个单位\n3. Pitch P同步调整\n\n我现在帮您调整参数..."
    }
  ]
}
```

### 数据质量要求

- ✅ 总数据量：10,000-50,000条对话
- ✅ 覆盖场景：90%以上常见调参场景
- ✅ 多语言：中文为主（70%），英文（30%）
- ✅ 多平台：PX4（60%），Betaflight（40%）
- ✅ 数据清洗：去除噪音、错误信息

---

## 🔧 微调流程

### 环境准备

```bash
# 1. 创建虚拟环境
conda create -n hkaic_deepseek python=3.10
conda activate hkaic_deepseek

# 2. 安装依赖
pip install torch
pip install transformers>=4.36.0
pip install peft>=0.7.0
pip install trl>=0.7.0
pip install bitsandbytes
pip install accelerate
pip install datasets
pip install wandb

# 3. 验证安装
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```

### 配置文件

```yaml
# finetune_config.yaml
model:
  name: "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
  base_model_path: "./models/base"
  output_path: "./models/hkaic-tuned"

training:
  method: "lora"
  lora_r: 16
  lora_alpha: 32
  lora_dropout: 0.05
  target_modules:
    - "q_proj"
    - "k_proj"
    - "v_proj"
    - "o_proj"
  
  batch_size: 4
  gradient_accumulation_steps: 4
  learning_rate: 2e-4
  num_train_epochs: 3
  warmup_ratio: 0.1
  logging_steps: 10
  save_steps: 500
  eval_steps: 500

quantization:
  load_in_4bit: true
  bnb_4bit_compute_dtype: "float16"
  bnb_4bit_use_double_quant: true
  bnb_4bit_quant_type: "nf4"

data:
  train_path: "./data/train.jsonl"
  eval_path: "./data/eval.jsonl"
  max_length: 2048

hardware:
  gradient_checkpointing: true
  optim: "paged_adamw_32bit"
```

### 微调脚本

```python
#!/usr/bin/env python3
"""
HKAIC DeepSeek微调脚本
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer
from datasets import load_dataset

def load_model_and_tokenizer(model_name):
    """加载模型和分词器"""
    print(f"正在加载模型: {model_name}")
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=dict(load_in_4bit=True),
        device_map="auto"
    )
    
    model = prepare_model_for_kbit_training(model)
    
    return model, tokenizer

def configure_lora(model):
    """配置LoRA"""
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )
    
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    return model

def prepare_dataset(tokenizer, data_path):
    """准备数据集"""
    def format_instruction(example):
        return f"""### 问题:
{example['instruction']}

### 回答:
{example['response']}"""
    
    dataset = load_dataset("json", data_files=data_path)
    dataset = dataset.map(lambda x: {
        "text": format_instruction(x)
    })
    
    return dataset

def train():
    """执行微调"""
    # 加载模型
    model_name = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
    model, tokenizer = load_model_and_tokenizer(model_name)
    model = configure_lora(model)
    
    # 准备数据
    train_dataset = prepare_dataset(tokenizer, "./data/train.jsonl")
    eval_dataset = prepare_dataset(tokenizer, "./data/eval.jsonl")
    
    # 训练参数
    training_args = TrainingArguments(
        output_dir="./output/hkaic-tuned",
        num_train_epochs=3,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        warmup_ratio=0.1,
        logging_steps=10,
        save_steps=500,
        eval_steps=500,
        evaluation_strategy="steps",
        save_total_limit=3,
        bf16=True,
        tf32=True,
        optim="paged_adamw_32bit",
    )
    
    # 创建训练器
    trainer = SFTTrainer(
        model=model,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        args=training_args,
        tokenizer=tokenizer,
        max_seq_length=2048,
    )
    
    # 开始训练
    print("开始微调训练...")
    trainer.train()
    
    # 保存模型
    print("保存微调模型...")
    trainer.save_model("./models/hkaic-tuned")
    
    return model, tokenizer

if __name__ == "__main__":
    train()
```

### 开始训练

```bash
# 单GPU训练
python finetune_hkaic.py

# 多GPU训练 (推荐)
torchrun --nproc_per_node=2 finetune_hkaic.py

# 使用wandb监控
wandb login
python finetune_hkaic.py --use_wandb
```

---

## 🚀 部署方案

### 方案1：本地部署 (推荐个人用户)

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

class HKAICLocal:
    def __init__(self, model_path="./models/hkaic-tuned"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            quantization_config=dict(load_in_4bit=True),
            device_map="auto"
        )
    
    def generate(self, prompt, max_length=512):
        inputs = self.tokenizer(prompt, return_tensors="pt").to("cuda")
        
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_length,
            temperature=0.7,
            top_p=0.9,
            do_sample=True
        )
        
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    def analyze(self, user_input):
        prompt = f"""你是HKAIC智能调参助手。请根据用户描述分析调参建议。

用户：{user_input}

分析："""
        
        response = self.generate(prompt)
        return self.parse_response(response)

# 使用示例
hkaic = HKAICLocal()
suggestion = hkaic.analyze("飞机太灵敏了")
print(suggestion)
```

### 方案2：API服务部署 (推荐企业用户)

```bash
# 使用vLLM部署高性能API
pip install vllm

# 启动服务
vllm serve hkaic/deepseek-r1-tuned \
  --tensor-parallel-size 2 \
  --port 8000 \
  --max-model-len 4096
```

```python
# API调用示例
import openai

client = openai.OpenAI(
    api_key="dummy",
    base_url="http://localhost:8000/v1"
)

response = client.chat.completions.create(
    model="hkaic-tuned",
    messages=[
        {"role": "system", "content": "你是HKAIC调参助手"},
        {"role": "user", "content": "飞机在高速飞行时抖动"}
    ]
)

print(response.choices[0].message.content)
```

### 方案3：云端部署 (适合大规模应用)

**推荐云服务商：**
- AWS (EC2 + SageMaker)
- 阿里云 (PAI + GPU实例)
- 腾讯云 (TI-ONE)
- Google Cloud (Vertex AI)

---

## 📈 性能评估

### 评估指标

#### 1. 调参准确率

```python
# 测试用例
test_cases = [
    {
        "input": "飞机太灵敏了",
        "expected_keywords": ["降低P值", "减少", "响应速度"]
    },
    {
        "input": "高速飞行时抖动", 
        "expected_keywords": ["增加D值", "阻尼", "振荡"]
    },
    {
        "input": "起飞时有漂移",
        "expected_keywords": ["增加I值", "积分", "消除漂移"]
    }
]

def evaluate_accuracy(model, test_cases):
    correct = 0
    for case in test_cases:
        response = model.analyze(case["input"])
        if any(keyword in response for keyword in case["expected_keywords"]):
            correct += 1
    
    accuracy = correct / len(test_cases) * 100
    return accuracy
```

#### 2. 响应速度

| 场景 | 目标响应时间 | 测量方法 |
|------|------------|---------|
| 简单查询 | <1秒 | 首次token到完成 |
| 参数分析 | <3秒 | 包含多轮推理 |
| 批量处理 | <10秒 | 10个参数分析 |

#### 3. 用户满意度

- A/B测试对比
- 用户评分系统
- 调参成功率统计

### 评估结果模板

```markdown
## HKAIC模型评估报告

### 基础信息
- 模型版本: v1.0.0
- 训练日期: 2026-05-21
- 参数量: 7B (LoRA: 16M)

### 性能指标
- 调参准确率: 92.5%
- 响应时间: P95 < 2.5s
- 用户满意度: 4.6/5.0

### 详细测试结果
[详细测试数据表格]

### 改进建议
[优化方向列表]
```

---

## 🔄 持续优化

### 数据反馈循环

```
用户使用 → 数据收集 → 质量筛选 → 模型优化 → 重新部署
    ↑                                              ↓
    └──────────────────────────────────────────────┘
```

### 自动化优化流程

```yaml
# .github/workflows/model-update.yml
name: Model Update Pipeline

on:
  schedule:
    - cron: '0 2 * * 0'  # 每周日凌晨2点
  workflow_dispatch:

jobs:
  update-model:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Collect New Data
        run: python scripts/collect_feedback.py
      
      - name: Data Quality Check
        run: python scripts/quality_filter.py
        
      - name: Fine-tune Model
        run: python finetune_hkaic.py
        
      - name: Evaluate Model
        run: python scripts/evaluate.py
        
      - name: Deploy if Passed
        if: success()
        run: python scripts/deploy.py
```

### 版本管理

| 版本 | 日期 | 主要改进 | 准确率 |
|------|------|---------|-------|
| v1.0.0 | 2026-05-21 | 初始版本 | 85% |
| v1.1.0 | (计划中) | 增加Betaflight支持 | 88% |
| v2.0.0 | (计划中) | 专业级调参模型 | 95% |

---

## 📝 附录

### A. 常见问题

**Q: 训练需要多长时间？**
A: 使用RTX 4090，约4-8小时完成3个epoch训练。

**Q: 可以使用免费的GPU吗？**
A: 可以使用Google Colab (T4)或Kaggle (P100)，但训练时间会更长。

**Q: 如何处理中文和英文混合？**
A: 使用中英双语数据集训练，tokenizer需支持两种语言。

### B. 参考资源

- [DeepSeek官方GitHub](https://github.com/deepseek-ai)
- [Hugging Face Transformers文档](https://huggingface.co/docs/transformers)
- [PEFT微调指南](https://github.com/huggingface/peft)
- [TRL强化学习训练](https://github.com/huggingface/trl)

### C. 联系方式

- GitHub Issues: [提交Bug或建议](https://github.com/hkaic/hkaic/issues)
- Discord: [加入讨论群](https://discord.gg/hkaic)
- Email: support@hkaic.com

---

*最后更新: 2026-05-21*
*版本: 1.0.0*
