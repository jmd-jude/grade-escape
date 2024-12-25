# Grade Escape MVP

A scalable grading service that uses AI to help teachers grade handwritten student responses efficiently and consistently.

## Features

- 📝 OCR for handwritten text
- 🤖 AI-powered grading with rubric alignment
- 📊 Detailed feedback generation
- 🔄 Batch processing support
- 📱 Mobile-friendly interface

## Local Development Setup

1. Clone the repository:
```bash
git clone [your-repo-url]
cd grade-escape-mvp
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with required environment variables:
```env
OPENAI_API_KEY=your_openai_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_SERVICE_KEY=your_supabase_service_key
STORAGE_BUCKET=ap-grader-images
```

5. Run the application:
```bash
streamlit run app.py
```

## Deployment to Streamlit Cloud

1. Push your code to GitHub
2. Connect your repository to Streamlit Cloud
3. Add the following secrets in Streamlit Cloud settings:
   - `OPENAI_API_KEY`
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `SUPABASE_SERVICE_KEY`
   - `STORAGE_BUCKET`

## Project Structure

```
grade-escape-mvp/
├── app.py                 # Main Streamlit application
├── config/               
│   └── settings.py        # Configuration management
├── models/                # Data models
├── services/             # Business logic
│   ├── grading.py        # Grading service
│   ├── ocr_service.py    # OCR processing
│   └── storage.py        # Storage service
├── ui/                   # UI components
│   ├── components/       # Reusable UI components
│   └── pages/           # Page layouts
└── utils/                # Utility functions
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for GPT-4 | Yes |
| `SUPABASE_URL` | Supabase project URL | Yes |
| `SUPABASE_KEY` | Supabase anon/public key | Yes |
| `SUPABASE_SERVICE_KEY` | Supabase service role key | Yes |
| `STORAGE_BUCKET` | Supabase storage bucket name | Yes |
| `ENVIRONMENT` | Deployment environment (development/production) | No |
| `DEBUG` | Enable debug mode (True/False) | No |

## Contributing

1. Create a feature branch
2. Make your changes
3. Submit a pull request

## License

[Your chosen license]
