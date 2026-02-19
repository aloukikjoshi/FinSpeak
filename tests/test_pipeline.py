"""
Unit tests for FinSpeak pipeline
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from fin_speak.nlp import detect_intent, extract_fund, extract_time_period
from fin_speak.kb import (
    match_fund,
    compute_return,
    get_latest_nav,
    get_fund_info,
    load_funds_data,
    load_nav_data,
    search_funds,
)
from fin_speak.app import generate_answer


class TestNLP:
    """Tests for NLP module"""
    
    def test_detect_intent_nav(self):
        """Test intent detection for NAV queries"""
        transcript = "What is the current NAV of Vanguard S&P 500 Fund?"
        result = detect_intent(transcript)
        
        assert result['intent'] == 'get_nav'
        assert result['confidence'] > 0.5
    
    def test_detect_intent_return(self):
        """Test intent detection for return queries"""
        transcript = "Show me 6 month returns for Fidelity Growth Fund"
        result = detect_intent(transcript)
        
        assert result['intent'] == 'get_return'
        assert result['confidence'] > 0.5
        assert result['period_months'] == 6
    
    def test_detect_intent_explain(self):
        """Test intent detection for explanation queries"""
        transcript = "Why did the fund price change?"
        result = detect_intent(transcript)
        
        assert result['intent'] == 'explain_change'
    
    def test_extract_time_period(self):
        """Test time period extraction"""
        assert extract_time_period("6 month returns") == 6
        assert extract_time_period("1 year performance") == 12
        assert extract_time_period("2 year returns") == 24
    
    def test_extract_fund_with_list(self):
        """Test fund extraction with provided list"""
        fund_names = [
            "Vanguard S&P 500 Index Fund",
            "Fidelity Growth Company Fund"
        ]
        
        transcript = "What is the NAV of Vanguard S&P 500?"
        fund_name, confidence = extract_fund(transcript, fund_names)
        
        assert fund_name is not None
        assert "Vanguard" in fund_name
        assert confidence > 0.5


class TestKB:
    """Tests for Knowledge Base module"""
    
    def test_load_funds_data(self):
        """Test loading funds data"""
        df = load_funds_data()
        
        assert not df.empty
        assert 'fund_id' in df.columns
        assert 'fund_name' in df.columns
        assert len(df) == 10  # We have 10 funds
    
    def test_load_nav_data(self):
        """Test loading NAV data"""
        df = load_nav_data()
        
        assert not df.empty
        assert 'fund_id' in df.columns
        assert 'date' in df.columns
        assert 'nav' in df.columns
    
    def test_match_fund_exact(self):
        """Test exact fund matching"""
        fund_id = match_fund("Vanguard S&P 500 Index Fund")
        
        assert fund_id is not None
        assert fund_id == "F001"
    
    def test_match_fund_fuzzy(self):
        """Test fuzzy fund matching"""
        fund_id = match_fund("Vanguard S&P 500")
        
        assert fund_id is not None
        assert fund_id == "F001"
    
    def test_get_latest_nav(self):
        """Test getting latest NAV"""
        nav_data = get_latest_nav("F001")
        
        assert nav_data is not None
        assert 'date' in nav_data
        assert 'nav' in nav_data
        assert nav_data['nav'] > 0
    
    def test_get_fund_info(self):
        """Test getting fund information"""
        fund_info = get_fund_info("F001")
        
        assert fund_info is not None
        assert fund_info['fund_name'] == "Vanguard S&P 500 Index Fund"
        assert fund_info['ticker'] == "VFIAX"
    
    def test_compute_return(self):
        """Test return computation"""
        return_data = compute_return("F001", months=6)
        
        assert return_data is not None
        assert 'start_date' in return_data
        assert 'end_date' in return_data
        assert 'start_nav' in return_data
        assert 'end_nav' in return_data
        assert 'percentage_return' in return_data
        assert 'absolute_return' in return_data
    
    def test_compute_return_12_months(self):
        """Test return computation for 12 months"""
        return_data = compute_return("F001", months=12)
        
        assert return_data is not None
        assert return_data['period_months'] >= 11  # Allow some tolerance
        assert return_data['period_months'] <= 13
    
    def test_compute_return_invalid_fund(self):
        """Test return computation with invalid fund"""
        with pytest.raises(ValueError):
            compute_return("INVALID_FUND", months=12)


class TestSTT:
    """Tests for STT module"""
    
    def test_transcribe_local_mocked(self):
        """Test local transcription (mocked)"""
        import sys
        
        # Create mock whisper module
        mock_whisper = MagicMock()
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            'text': 'What is the current NAV?'
        }
        mock_whisper.load_model.return_value = mock_model
        
        # Patch whisper in sys.modules before import
        with patch.dict(sys.modules, {'whisper': mock_whisper}):
            # Also mock torch for cuda check
            mock_torch = MagicMock()
            mock_torch.cuda.is_available.return_value = False
            with patch.dict(sys.modules, {'torch': mock_torch}):
                from fin_speak.stt import transcribe_local
                result = transcribe_local("dummy.wav")
        
        assert result == 'What is the current NAV?'
        mock_whisper.load_model.assert_called_once()
        mock_model.transcribe.assert_called_once()


class TestTTS:
    """Tests for TTS module"""
    
    def test_synthesize_gtts_mocked(self):
        """Test gTTS synthesis (mocked)"""
        import sys
        
        # Create mock gtts module
        mock_gtts_module = MagicMock()
        mock_tts_instance = MagicMock()
        mock_gtts_module.gTTS.return_value = mock_tts_instance
        
        # Patch gtts in sys.modules before import
        with patch.dict(sys.modules, {'gtts': mock_gtts_module}):
            from fin_speak.tts import synthesize_gtts
            synthesize_gtts("Test text", "/tmp/test.mp3")
        
        mock_gtts_module.gTTS.assert_called_once()
        mock_tts_instance.save.assert_called_once_with("/tmp/test.mp3")


class TestIntegration:
    """Integration tests for the full pipeline"""
    
    def test_full_pipeline_nav_query(self):
        """Test full pipeline for NAV query"""
        # Input
        transcript = "What is the current NAV of Vanguard S&P 500 Fund?"
        
        # Detect intent
        intent_result = detect_intent(transcript)
        assert intent_result['intent'] == 'get_nav'
        
        # Extract fund
        fund_name, _ = extract_fund(transcript)
        assert fund_name is not None
        
        # Match fund
        fund_id = match_fund(fund_name)
        assert fund_id == "F001"
        
        # Get NAV
        nav_data = get_latest_nav(fund_id)
        assert nav_data is not None
        assert nav_data['nav'] > 0
    
    def test_full_pipeline_return_query(self):
        """Test full pipeline for return query"""
        # Input
        transcript = "Show me 6 month returns for Vanguard S&P 500 Fund"
        
        # Detect intent
        intent_result = detect_intent(transcript)
        assert intent_result['intent'] == 'get_return'
        assert intent_result['period_months'] == 6
        
        # Extract fund
        fund_name, _ = extract_fund(transcript)
        assert fund_name is not None
        
        # Match fund
        fund_id = match_fund(fund_name)
        assert fund_id == "F001"
        
        # Compute return
        return_data = compute_return(fund_id, months=6)
        assert return_data is not None
        assert 'percentage_return' in return_data


class TestGenerateAnswer:
    """Tests for answer generation"""
    
    def test_generate_answer_nav(self):
        """Test answer generation for NAV query"""
        nav_data = {'date': '2026-01-31', 'nav': 79.67}
        
        answer = generate_answer(
            transcript="What is the NAV of Vanguard S&P 500?",
            intent="get_nav",
            fund_id="F001",
            fund_name="Vanguard S&P 500 Index Fund",
            period_months=None,
            nav_data=nav_data,
            return_data=None,
        )
        
        assert "79.67" in answer
        assert "Vanguard S&P 500 Index Fund" in answer
        assert "2026-01-31" in answer
    
    def test_generate_answer_return(self):
        """Test answer generation for return query"""
        return_data = {
            'percentage_return': 15.5,
            'absolute_return': 10.23,
            'start_nav': 66.0,
            'end_nav': 76.23,
            'start_date': '2025-01-31',
            'end_date': '2026-01-31',
            'period_months': 12.0,
        }
        
        answer = generate_answer(
            transcript="Show me 12 month returns for Vanguard",
            intent="get_return",
            fund_id="F001",
            fund_name="Vanguard S&P 500 Index Fund",
            period_months=12,
            nav_data=None,
            return_data=return_data,
        )
        
        assert "15.5" in answer or "15.50" in answer
        assert "gained" in answer
        assert "Vanguard S&P 500 Index Fund" in answer
    
    def test_generate_answer_no_fund(self):
        """Test answer when fund is not found"""
        answer = generate_answer(
            transcript="What is the NAV of Unknown Fund?",
            intent="get_nav",
            fund_id=None,
            fund_name=None,
            period_months=None,
        )
        
        assert "couldn't identify" in answer.lower()
    
    def test_generate_answer_explain(self):
        """Test answer for explain_change intent"""
        answer = generate_answer(
            transcript="Why did the fund change?",
            intent="explain_change",
            fund_id="F001",
            fund_name="Vanguard S&P 500 Index Fund",
            period_months=None,
        )
        
        assert "performance" in answer.lower() or "analysis" in answer.lower()


class TestSearchFunds:
    """Tests for search_funds function"""
    
    def test_search_funds_by_name(self):
        """Test searching funds by name"""
        results = search_funds("Vanguard")
        
        assert len(results) >= 1
        assert any("Vanguard" in r['fund_name'] for r in results)
    
    def test_search_funds_by_category(self):
        """Test searching funds by category"""
        results = search_funds("Equity")
        
        assert len(results) >= 1
        assert all("Equity" in r['category'] for r in results)
    
    def test_search_funds_no_match(self):
        """Test search with no matches"""
        results = search_funds("NonexistentFundXYZ123")
        
        assert len(results) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
