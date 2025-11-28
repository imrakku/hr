def get_custom_css():
    return """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        * {
            font-family: 'Inter', sans-serif;
        }

        .iim-header {
            background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
            padding: 2.5rem 2rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }

        .iim-header h1 {
            color: white;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            text-align: center;
        }

        .iim-header p {
            color: #e0e7ff;
            font-size: 1.1rem;
            text-align: center;
            margin: 0;
        }

        .stButton>button {
            width: 100%;
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            color: white;
            border: none;
            padding: 0.75rem 2rem;
            font-size: 1rem;
            font-weight: 600;
            border-radius: 8px;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        }

        .metric-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            border-left: 4px solid #3b82f6;
            margin-bottom: 1rem;
        }

        .score-high {
            color: #10b981;
            font-weight: 700;
            font-size: 1.5rem;
        }

        .score-medium {
            color: #f59e0b;
            font-weight: 700;
            font-size: 1.5rem;
        }

        .score-low {
            color: #ef4444;
            font-weight: 700;
            font-size: 1.5rem;
        }

        .stExpander {
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            margin-bottom: 1rem;
            overflow: hidden;
        }

        .stExpander:hover {
            border-color: #3b82f6;
            box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
        }

        div[data-testid="stMetricValue"] {
            font-size: 2rem;
            font-weight: 700;
        }

        .uploadedFile {
            border: 2px dashed #3b82f6;
            border-radius: 8px;
            padding: 1rem;
            background: #eff6ff;
        }

        .stProgress > div > div > div {
            background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%);
        }

        h1, h2, h3 {
            color: #1e293b;
        }

        .stDataFrame {
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        }

        .info-box {
            background: #eff6ff;
            border-left: 4px solid #3b82f6;
            padding: 1rem;
            border-radius: 6px;
            margin: 1rem 0;
        }

        .success-box {
            background: #d1fae5;
            border-left: 4px solid #10b981;
            padding: 1rem;
            border-radius: 6px;
            margin: 1rem 0;
        }

        .warning-box {
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 1rem;
            border-radius: 6px;
            margin: 1rem 0;
        }
    </style>
    """
