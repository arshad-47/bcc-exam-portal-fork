import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from src.config import Config

class UIHelper:
    @staticmethod
    def inject_custom_css():
        """
        Injects custom CSS to enhance Streamlit UI:
        - Sleek container cards
        - Smooth hover animations
        - Modern typography and color badges
        - Sidebar adjustments
        """
        custom_css = """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
            
            /* Typography */
            html, body, [class*="css"] {
                font-family: 'Outfit', sans-serif;
            }
            
            /* Main header styling */
            .main-header {
                background: linear-gradient(135deg, #4F46E5 0%, #312E81 100%);
                padding: 2.5rem;
                border-radius: 16px;
                color: white;
                text-align: center;
                margin-bottom: 2rem;
                box-shadow: 0 10px 25px -5px rgba(79, 70, 229, 0.3);
            }
            .main-header h1 {
                color: #FFFFFF !important;
                font-size: 2.2rem !important;
                font-weight: 700 !important;
                margin-bottom: 0.5rem !important;
                letter-spacing: -0.025em;
            }
            .main-header p {
                font-size: 1.1rem;
                opacity: 0.9;
                font-weight: 300;
            }
            
            /* Card Containers */
            .premium-card {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #E2E8F0;
                padding: 1.5rem;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                margin-bottom: 1rem;
            }
            .premium-card:hover {
                transform: translateY(-4px);
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04);
                border-color: #CBD5E1;
            }
            
            /* Badges */
            .badge {
                display: inline-block;
                padding: 0.25rem 0.75rem;
                border-radius: 9999px;
                font-size: 0.85rem;
                font-weight: 600;
                text-align: center;
            }
            .badge-pass {
                background-color: #DCFCE7;
                color: #166534;
            }
            .badge-fail {
                background-color: #FEE2E2;
                color: #991B1B;
            }
            .badge-info {
                background-color: #E0F2FE;
                color: #075985;
            }
            
            /* Grade Badge circles */
            .grade-circle {
                display: flex;
                align-items: center;
                justify-content: center;
                width: 48px;
                height: 48px;
                border-radius: 50%;
                font-size: 1.3rem;
                font-weight: 700;
                color: white;
            }
            
            /* Custom metric styles */
            .metric-val {
                font-size: 2rem;
                font-weight: 700;
                color: #1E293B;
                margin-bottom: 0.2rem;
            }
            .metric-label {
                font-size: 0.9rem;
                color: #64748B;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
        </style>
        """
        st.markdown(custom_css, unsafe_allow_html=True)

    @staticmethod
    def render_header(title, subtitle):
        """
        Renders the styled hero header card
        """
        st.markdown(f"""
        <div class="main-header">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def card(title, content_html, footer_html=None):
        """
        Renders a premium shadow card container
        """
        footer = f"<div style='margin-top: 1rem; border-top: 1px solid #F1F5F9; padding-top: 0.5rem;'>{footer_html}</div>" if footer_html else ""
        st.markdown(f"""
        <div class="premium-card">
            <h3 style="margin-top:0; color:#1E3A8A; font-size:1.25rem; font-weight:600;">{title}</h3>
            <div>{content_html}</div>
            {footer}
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def render_metric(label, value, icon=""):
        """
        Renders a metric element inside a card
        """
        st.markdown(f"""
        <div class="premium-card" style="text-align: center;">
            <div style="font-size: 1.8rem; margin-bottom: 0.3rem;">{icon}</div>
            <div class="metric-val">{value}</div>
            <div class="metric-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)

    # --- PLOTLY ANALYTICS ---

    @staticmethod
    def plot_pass_fail_pie(results_df: pd.DataFrame):
        """
        Creates a pass/fail percentage donut chart
        """
        if results_df.empty:
            return None
            
        pass_counts = results_df['passed'].value_counts().reset_index()
        pass_counts['label'] = pass_counts['passed'].map({True: 'Passed', False: 'Failed'})
        
        fig = px.pie(
            pass_counts,
            values='count',
            names='label',
            hole=0.4,
            color='label',
            color_discrete_map={'Passed': '#10B981', 'Failed': '#EF4444'},
            title="Overall Pass / Fail Distribution"
        )
        fig.update_traces(textinfo='percent+label', pull=[0.05, 0])
        fig.update_layout(
            showlegend=False,
            margin=dict(t=40, b=10, l=10, r=10),
            height=260,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        return fig

    @staticmethod
    def plot_topic_performance_bar(results_responses: list):
        """
        Summarizes topic-wise averages across responses and builds a horizontal bar chart
        """
        if not results_responses:
            return None
            
        # Compile topic performance
        topic_data = []
        for resp in results_responses:
            topic_data.append({
                "topic": resp["question_bank"]["topic"],
                "is_correct": bool(resp["is_correct"])
            })
            
        df = pd.DataFrame(topic_data)
        if df.empty:
            return None
            
        grouped = df.groupby("topic")["is_correct"].mean().reset_index()
        grouped["percentage"] = grouped["is_correct"] * 100.0
        grouped = grouped.sort_values(by="percentage", ascending=True)
        
        fig = px.bar(
            grouped,
            x="percentage",
            y="topic",
            orientation="h",
            labels={"percentage": "Average Accuracy (%)", "topic": "Topics"},
            title="Topic Performance Breakdown",
            color="percentage",
            color_continuous_scale="Viridis"
        )
        fig.update_layout(
            xaxis=dict(range=[0, 100]),
            margin=dict(t=40, b=10, l=10, r=10),
            height=280,
            coloraxis_showscale=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        return fig

    @staticmethod
    def plot_exam_trends_line(results_df: pd.DataFrame):
        """
        Plots the average percentage score of exams taken over time
        """
        if results_df.empty:
            return None
            
        # Parse and format datetime
        df = results_df.copy()
        df['submitted_at'] = pd.to_datetime(df['submitted_at'])
        df['date'] = df['submitted_at'].dt.date
        
        grouped = df.groupby('date')['percentage'].mean().reset_index()
        grouped = grouped.sort_values(by='date')
        
        fig = px.line(
            grouped,
            x='date',
            y='percentage',
            title='Daily Average Exam Scores (%)',
            labels={'date': 'Date', 'percentage': 'Avg Score (%)'},
            markers=True
        )
        fig.update_traces(line_color='#4F46E5', line_width=3, marker=dict(size=8, color='#312E81'))
        fig.update_layout(
            yaxis=dict(range=[0, 105]),
            margin=dict(t=40, b=10, l=10, r=10),
            height=260,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        return fig

    @staticmethod
    def plot_difficulty_performance(results_responses: list):
        """
        Plots accuracy grouped by question difficulty level
        """
        if not results_responses:
            return None
            
        difficulty_data = []
        for resp in results_responses:
            difficulty_data.append({
                "difficulty": resp["question_bank"]["difficulty"],
                "is_correct": bool(resp["is_correct"])
            })
            
        df = pd.DataFrame(difficulty_data)
        if df.empty:
            return None
            
        grouped = df.groupby("difficulty")["is_correct"].mean().reset_index()
        grouped["accuracy"] = grouped["is_correct"] * 100.0
        
        # Define categorical ordering
        difficulty_order = {"Easy": 0, "Medium": 1, "Hard": 2}
        grouped["order"] = grouped["difficulty"].map(difficulty_order)
        grouped = grouped.sort_values(by="order")
        
        fig = px.bar(
            grouped,
            x="difficulty",
            y="accuracy",
            color="difficulty",
            color_discrete_map={"Easy": "#10B981", "Medium": "#F59E0B", "Hard": "#EF4444"},
            labels={"accuracy": "Accuracy (%)", "difficulty": "Difficulty Level"},
            title="Accuracy by Difficulty Level"
        )
        fig.update_layout(
            yaxis=dict(range=[0, 105]),
            showlegend=False,
            margin=dict(t=40, b=10, l=10, r=10),
            height=260,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        return fig
