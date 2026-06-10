from typing import List, Dict, Any

class EvaluationEngine:
    @staticmethod
    def calculate_grade(percentage: float) -> str:
        """
        Determines the grade based on percentage:
        S Grade: 90% and above
        A Grade: 80% - 89.99%
        B Grade: 70% - 79.99%
        C Grade: 60% - 69.99%
        D Grade: 50% - 59.99%
        E Grade: 40% - 49.99%
        F Grade (Fail): Below 40%
        """
        if percentage >= 90.0:
            return 'S'
        elif percentage >= 80.0:
            return 'A'
        elif percentage >= 70.0:
            return 'B'
        elif percentage >= 60.0:
            return 'C'
        elif percentage >= 50.0:
            return 'D'
        elif percentage >= 40.0:
            return 'E'
        else:
            return 'F'

    @staticmethod
    def evaluate_exam(questions: List[Dict[str, Any]], student_answers: Dict[int, str], passing_percentage: float = 40.0) -> Dict[str, Any]:
        """
        Evaluates exam submissions.
        
        Args:
            questions: List of question dicts from question_bank
            student_answers: Dict of {question_id: selected_option_str}
            passing_percentage: Minimum percentage needed to pass
            
        Returns:
            Dict containing:
                - score: total correct answers (int)
                - total_questions: number of questions evaluated (int)
                - percentage: score percentage (float)
                - grade: computed grade (str)
                - passed: True/False (bool)
                - topic_analysis: Dict of topic-wise performance breakdowns
                - response_details: List of dicts mapping each response for db insertion
        """
        score = 0
        total_questions = len(questions)
        
        # Topic analysis storage: {topic: {'total': int, 'correct': int}}
        topic_map = {}
        response_details = []
        
        for q in questions:
            q_id = q['id']
            topic = q['topic']
            correct_opt = q['correct_option'].strip().upper()
            
            # Retrieve answer, default to empty/unanswered
            selected_opt = student_answers.get(q_id, "").strip().upper()
            
            is_correct = (selected_opt == correct_opt)
            if is_correct:
                score += 1
                
            # Track topic stats
            if topic not in topic_map:
                topic_map[topic] = {'total': 0, 'correct': 0}
            
            topic_map[topic]['total'] += 1
            if is_correct:
                topic_map[topic]['correct'] += 1
                
            # Log response detail for DB insert
            response_details.append({
                "question_id": q_id,
                "selected_option": selected_opt if selected_opt else "-",
                "is_correct": is_correct
            })
            
        # Overall percentage & pass status
        percentage = (score / total_questions * 100.0) if total_questions > 0 else 0.0
        grade = EvaluationEngine.calculate_grade(percentage)
        passed = (percentage >= passing_percentage)
        
        # Format topic performance
        topic_analysis = {}
        for topic, stats in topic_map.items():
            tot = stats['total']
            corr = stats['correct']
            acc = (corr / tot * 100.0) if tot > 0 else 0.0
            topic_analysis[topic] = {
                "total": tot,
                "correct": corr,
                "accuracy": round(acc, 2)
            }
            
        # Group modules for the Unified Exam
        bcc_topics = ['Computer Fundamentals', 'Operating Systems', 'Internet & Web']
        msoffice_topics = ['MS Word', 'MS Excel', 'MS PowerPoint']
        
        def _get_module_grade(topics_list):
            m_total = sum(topic_map.get(t, {}).get('total', 0) for t in topics_list)
            m_corr = sum(topic_map.get(t, {}).get('correct', 0) for t in topics_list)
            if m_total > 0:
                m_perc = (m_corr / m_total) * 100.0
                return EvaluationEngine.calculate_grade(m_perc)
            return "N/A"
            
        bcc_grade = _get_module_grade(bcc_topics)
        msoffice_grade = _get_module_grade(msoffice_topics)

        return {
            "score": score,
            "total_questions": total_questions,
            "percentage": round(percentage, 2),
            "grade": grade,
            "passed": passed,
            "topic_analysis": topic_analysis,
            "response_details": response_details,
            "bcc_grade": bcc_grade,
            "msoffice_grade": msoffice_grade
        }

    @staticmethod
    def evaluate_typing_test(expected_text: str, typed_text: str, duration_minutes: float) -> Dict[str, Any]:
        """
        Evaluates typing test performance.
        WPM = (Total characters typed / 5) / duration
        Accuracy = (Correctly typed characters / Total expected characters) * 100
        """
        expected_words = expected_text.strip().split()
        typed_words = typed_text.strip().split()
        
        correct_chars = 0
        total_typed_chars = len(typed_text)
        
        # Simple word-by-word comparison for accuracy (can be refined later)
        for i, expected_word in enumerate(expected_words):
            if i < len(typed_words) and typed_words[i] == expected_word:
                correct_chars += len(expected_word) + 1 # +1 for space
                
        # Gross WPM formula
        wpm = int((total_typed_chars / 5) / duration_minutes) if duration_minutes > 0 else 0
        
        # Accuracy based on correct words/chars
        expected_chars_total = len(expected_text)
        accuracy = (correct_chars / expected_chars_total * 100.0) if expected_chars_total > 0 else 0.0
        
        return {
            "wpm": max(0, wpm),
            "accuracy": min(100.0, max(0.0, round(accuracy, 2)))
        }
