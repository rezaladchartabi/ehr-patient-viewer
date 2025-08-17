# Ollama Setup Guide

This guide shows you how to set up Ollama to run local LLMs for the medical chatbot without requiring any API keys.

## What is Ollama?

Ollama is a local LLM server that allows you to run large language models on your own machine. It's free, private, and doesn't require any API keys.

## Installation

### 1. Install Ollama

**macOS:**
```bash
# Download and install from https://ollama.ai
# Or use Homebrew:
brew install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows:**
- Download from https://ollama.ai
- Install the Windows version

### 2. Start Ollama

```bash
ollama serve
```

This starts the Ollama server on `http://localhost:11434`

### 3. Pull a Model

Choose one of these models (recommended in order):

```bash
# Llama 2 (7B parameters, good balance of speed/quality)
ollama pull llama2

# Mistral (7B parameters, excellent performance)
ollama pull mistral

# Phi-2 (2.7B parameters, very fast, good for simple tasks)
ollama pull phi

# Gemma (2B parameters, fast and efficient)
ollama pull gemma2:2b
```

## Configuration

### 1. Environment Variables

Create a `.env` file in the `backend` directory:

```bash
# NLP Configuration
NLP_TYPE=ollama

# Ollama Configuration (optional, defaults shown)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

### 2. Test the Setup

Run the test script to verify everything works:

```bash
cd backend
python3 test_ollama_nlp.py
```

## Model Comparison

| Model | Size | Speed | Quality | RAM Usage | Best For |
|-------|------|-------|---------|-----------|----------|
| **Llama 2** | 7B | Medium | High | 8GB | General use |
| **Mistral** | 7B | Fast | Very High | 8GB | Best overall |
| **Phi-2** | 2.7B | Very Fast | Good | 4GB | Simple queries |
| **Gemma 2B** | 2B | Very Fast | Good | 4GB | Resource-constrained |

## Performance Tips

### 1. Choose the Right Model

- **For development/testing**: Use `phi` or `gemma2:2b` (faster)
- **For production**: Use `mistral` or `llama2` (better quality)

### 2. System Requirements

- **Minimum**: 4GB RAM, 2GB free disk space
- **Recommended**: 8GB RAM, 5GB free disk space
- **Optimal**: 16GB RAM, 10GB free disk space

### 3. GPU Acceleration (Optional)

If you have a compatible GPU:

```bash
# Install CUDA version (if you have NVIDIA GPU)
ollama pull llama2:7b-cuda

# Install Metal version (if you have Apple Silicon)
ollama pull llama2:7b-metal
```

## Troubleshooting

### Common Issues

1. **"Ollama server not available"**
   ```bash
   # Start Ollama
   ollama serve
   ```

2. **"Model not found"**
   ```bash
   # List available models
   ollama list
   
   # Pull the model
   ollama pull llama2
   ```

3. **Slow responses**
   - Try a smaller model: `ollama pull phi`
   - Check available RAM
   - Close other applications

4. **High memory usage**
   - Use a smaller model
   - Restart Ollama: `pkill ollama && ollama serve`

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('chatbot.ollama_nlp_processor').setLevel(logging.DEBUG)
```

## Advanced Configuration

### Custom Model Configuration

You can create custom model configurations:

```bash
# Create a custom model file
cat > llama2-medical.modelfile << EOF
FROM llama2
SYSTEM "You are a medical AI assistant specialized in healthcare queries."
PARAMETER temperature 0.1
PARAMETER top_p 0.9
EOF

# Create the custom model
ollama create llama2-medical llama2-medical.modelfile
```

### Multiple Models

You can run multiple models simultaneously:

```bash
# Pull different models
ollama pull llama2
ollama pull mistral
ollama pull phi

# The system will use the first available model
```

## Security and Privacy

### Advantages of Ollama

- **No API keys required**
- **No data sent to external servers**
- **Complete privacy**
- **No usage limits**
- **No costs**

### Considerations

- **Local resource usage**: Uses CPU/RAM on your machine
- **Model updates**: Manual updates required
- **Model quality**: May be lower than GPT-4 for complex tasks

## Integration with the Chatbot

The chatbot automatically detects and uses Ollama when:

1. `NLP_TYPE=ollama` is set in environment
2. `NLP_TYPE=auto` and no OpenAI API key is available
3. Ollama server is running and accessible

### Fallback Behavior

If Ollama is unavailable, the system automatically falls back to:
1. Rule-based NLP (if available)
2. Error message (if no fallback available)

## Monitoring

### Check Ollama Status

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# List running models
ollama list

# Check model usage
ollama ps
```

### Logs

Ollama logs are available at:
- **macOS/Linux**: `~/.ollama/logs/ollama.log`
- **Windows**: `%USERPROFILE%\.ollama\logs\ollama.log`

## Next Steps

1. **Install Ollama**: Follow the installation steps above
2. **Test the setup**: Run `python3 test_ollama_nlp.py`
3. **Start the chatbot**: The system will automatically use Ollama
4. **Monitor performance**: Check logs and adjust model as needed

## Support

- **Ollama Documentation**: https://ollama.ai/docs
- **Ollama GitHub**: https://github.com/ollama/ollama
- **Community**: https://github.com/ollama/ollama/discussions
