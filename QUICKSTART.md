# MEDUROAM Quick Start - 5 Minute Setup

## Step 1: Install Dependencies (30 seconds)

```bash
pip install google-generativeai
```

## Step 2: Get API Key (2 minutes)

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the key

## Step 3: Run MEDUROAM (30 seconds)

### Option A: Set environment variable

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="your_api_key_here"
python meduroam.py
```

**Windows (CMD):**
```cmd
set GEMINI_API_KEY=your_api_key_here
python meduroam.py
```

**Mac/Linux:**
```bash
export GEMINI_API_KEY="your_api_key_here"
python meduroam.py
```

### Option B: Enter key when prompted

```bash
python meduroam.py
# When prompted, paste your API key
```

## Step 4: Use the System

1. **Start consultation**: MEDUROAM greets you
2. **Describe symptoms**: Type naturally
3. **Answer questions**: Follow the interview
4. **Generate SOAP note**: Type `SOAP` when done
5. **Exit safely**: Type `EXIT` to save and quit

## Example Session

```
You: I've had a bad headache for 3 days

MEDUROAM: I'm sorry to hear about your headache. Let me help you organize 
this information. Can you describe the headache for me? Is it throbbing, 
sharp, pressure-like, or something else?

You: It's throbbing and on one side

[... conversation continues ...]

You: SOAP

📋 Generating SOAP note...
[JSON output with full clinical documentation]

You: EXIT
✅ Session saved
```

## Important Notes

- ⚠️ **Red flags = immediate escalation** (chest pain, stroke symptoms, etc.)
- 📋 **All sessions auto-save** to `sessions/` folder
- 🔒 **Never share real PHI** (this is MVP, not HIPAA-compliant yet)
- 👨‍⚕️ **Requires doctor review** - this is a reasoning assistant, not a diagnosis

## Troubleshooting

**"Module not found"**
```bash
pip install google-generativeai
```

**"API key invalid"**
- Verify key at [AI Studio](https://makersuite.google.com/app/apikey)
- Check for extra spaces when pasting

**"Rate limit exceeded"**
- Free tier has limits; wait or upgrade to paid tier

## Commands During Consultation

- `SOAP` - Generate SOAP note
- `EXIT` - Save and quit
- `Ctrl+C` - Interrupt and save

---

**Total setup time: ~5 minutes**

Ready to deploy to production? See [Implementation Guide](docs/implementation_guide.md) for HIPAA compliance, database integration, and human-in-the-loop workflow.
