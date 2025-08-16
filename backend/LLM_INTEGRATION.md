# LLM Integration with GPT-4

This document explains how to set up and use GPT-4 for natural language processing in the medical chatbot.

## Overview

The chatbot now supports two NLP approaches:

1. **LLM-based (GPT-4)** - Uses OpenAI's GPT-4 for intent classification and entity extraction
2. **Rule-based** - Uses regex patterns and keyword matching (fallback)

## Setup

### 1. Get OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create an account or sign in
3. Generate a new API key
4. Copy the API key

### 2. Configure Environment Variables

Create a `.env` file in the `backend` directory:

```bash
# OpenAI API Configuration
OPENAI_API_KEY=your-openai-api-key-here

# NLP Configuration (set to "false" to use rule-based NLP)
USE_LLM_NLP=true
```

### 3. Install Dependencies

```bash
cd backend
pip install openai==1.3.7
```

## Features

### Intent Classification

GPT-4 can understand complex medical queries and classify them into:

- `medication_query` - Questions about medications, drugs, prescriptions
- `condition_query` - Questions about medical conditions, diagnoses, PMH
- `observation_query` - Questions about vital signs, lab results, measurements
- `encounter_query` - Questions about hospital visits, appointments
- `procedure_query` - Questions about medical procedures, surgeries
- `specimen_query` - Questions about lab samples, specimens
- `allergy_query` - Questions about allergies, reactions
- `interaction_query` - Questions about drug interactions
- `evidence_query` - Questions about clinical evidence, studies
- `alert_query` - Questions about clinical alerts, warnings
- `general_query` - General medical questions

### Entity Extraction

GPT-4 extracts medical entities like:
- Medication names
- Medical conditions
- Allergies
- Procedures
- Vital signs
- Lab tests
- Symptoms
- Body parts

### Context Analysis

GPT-4 analyzes query context:
- Time references (current, recent, past, future)
- Severity levels (mild, moderate, severe)
- Urgency indicators (urgent, routine)
- Comparison types (trend, baseline, normal)

### Query Complexity Analysis

GPT-4 analyzes query complexity:
- Complexity level (simple, moderate, complex)
- Whether context is required
- Multi-intent detection
- Medical terminology density

## Testing

Run the test script to verify LLM integration:

```bash
cd backend
python test_llm_nlp.py
```

## Fallback Behavior

If GPT-4 is unavailable or fails:
1. The system automatically falls back to rule-based NLP
2. All functionality continues to work
3. Error messages are logged for debugging

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | None | Your OpenAI API key |
| `USE_LLM_NLP` | `true` | Enable/disable LLM-based NLP |

### API Configuration

The LLM processor uses these settings:
- **Model**: `gpt-4`
- **Temperature**: `0.1` (low for consistent results)
- **Max Tokens**: `200` (sufficient for medical queries)

## Cost Considerations

GPT-4 API costs:
- **Input tokens**: ~$0.03 per 1K tokens
- **Output tokens**: ~$0.06 per 1K tokens
- **Typical query**: ~100-200 tokens total
- **Estimated cost**: ~$0.01-0.02 per query

## Security

- API keys are stored in environment variables
- No API keys are logged or stored in code
- Fallback to rule-based NLP if API is unavailable
- Error handling prevents API key exposure

## Performance

### LLM-based NLP
- **Pros**: Better understanding, handles complex queries, natural language
- **Cons**: API latency (~1-2 seconds), requires internet, costs money

### Rule-based NLP
- **Pros**: Fast, no API calls, no costs, works offline
- **Cons**: Limited to predefined patterns, less flexible

## Troubleshooting

### Common Issues

1. **"OPENAI_API_KEY not found"**
   - Check your `.env` file
   - Verify the API key is correct
   - Restart the server

2. **"Failed to initialize LLM processor"**
   - Check internet connection
   - Verify API key is valid
   - Check OpenAI service status

3. **High latency**
   - Consider using rule-based NLP for simple queries
   - Implement caching for repeated queries
   - Use GPT-3.5-turbo for faster responses

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('chatbot.llm_nlp_processor').setLevel(logging.DEBUG)
```

## Migration from Rule-based

The system automatically handles migration:
1. If LLM is available, it's used by default
2. If LLM fails, it falls back to rule-based
3. No code changes required
4. Both approaches use the same interface

## Future Enhancements

- Fine-tuning on medical conversations
- Local LLM support (Llama, Mistral)
- Medical-specific models (Med-PaLM, BioGPT)
- Conversation memory and context
- Multi-language support
