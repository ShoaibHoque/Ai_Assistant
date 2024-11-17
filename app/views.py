from flask import Blueprint, render_template, request, jsonify
from .voice_processing import VoiceProcessor
from .nlu_processing import NLUProcessor
from .erp_data import ERPData
import whisper
import pandas as pd

# Initialize components
whisper_model = whisper.load_model("base", device="cpu")
voice_processor = VoiceProcessor(whisper_model)
nlu_processor = NLUProcessor()
erp_data = ERPData()
session_data = {}

main = Blueprint('main', __name__)

@main.route('/')
def index():
    try:
        df = pd.read_csv("requests_db.csv")
        csv_data = df.to_html(classes="striped highlight", index=False)
    except FileNotFoundError:
        csv_data = "<p>No records found.</p>"
    return render_template('index.html', csv_data=csv_data)

@main.route('/record', methods=['POST'])
def record_audio():
    try:
        # Record and transcribe
        audio = voice_processor.record_audio(duration=15)
        text, language = voice_processor.transcribe_audio(audio)
        session_data['transcription'] = text
        session_data['language'] = language
        return jsonify({"message": "Audio recorded successfully", "transcription": text, "language": language}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route('/process', methods=['POST'])
def process_request():
    try:
        transcription = session_data.get('transcription', '')
        language = session_data.get('language', 'en')

        if not transcription:
            return jsonify({"error": "No transcription available. Please record audio first."}), 400

        intent_data = nlu_processor.parse_intent_and_entities(transcription, lang=language)
        session_data['intent_data'] = intent_data

        # Detect missing fields
        required_fields = ["PROJECT_NAME", "AMOUNT", "REASON"]
        missing_fields = [field for field in required_fields if not intent_data["entities"].get(field)]

        # Generate confirmation text
        confirmation_text = (
            f"You are requesting money for project {intent_data['entities'].get('PROJECT_NAME', 'Unknown')} "
            f"with an amount of {intent_data['entities'].get('AMOUNT', 'Unknown')} "
            f"for {intent_data['entities'].get('REASON', 'Unknown')}. "
            f"Do you want to proceed?"
        )

        return jsonify({
            "message": "Processed successfully",
            "intent_data": intent_data,
            "missing_fields": missing_fields,
            "confirmation_text": confirmation_text
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main.route('/fill_missing', methods=['POST'])
def fill_missing():
    try:
        field_to_fill = request.json.get("field")
        language = session_data.get('language', 'en')

        # Prompt user for the missing field via voice
        prompt = f"Please provide the {field_to_fill.replace('_', ' ').lower()}."
        voice_processor.synthesize_speech(prompt, lang=language)

        # Record and process the user's response
        audio = voice_processor.record_audio(duration=10)
        response, _ = voice_processor.transcribe_audio(audio)

        # Update session data
        intent_data = session_data.get('intent_data', {})
        intent_data["entities"][field_to_fill] = response
        session_data['intent_data'] = intent_data

        # Check if all fields are now filled
        required_fields = ["PROJECT_NAME", "AMOUNT", "REASON"]
        missing_fields = [field for field in required_fields if not intent_data["entities"].get(field)]

        return jsonify({
            "message": f"{field_to_fill} filled successfully",
            "intent_data": intent_data,
            "missing_fields": missing_fields
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route('/confirm', methods=['POST'])
def confirm_request():
    try:
        intent_data = session_data.get('intent_data', {})
        language = session_data.get('language', 'en')

        if not intent_data:
            return jsonify({"error": "No intent data available. Please process the request first."}), 400

        confirmation = request.json.get('confirmation', '').lower()
        if confirmation in ['yes', 'y', 'ok', 'confirm']:
            result = erp_data.add_request("Employee123", intent_data, lang=language)
            return jsonify({"message": "Request confirmed and saved", "result": result}), 200
        elif confirmation in ['no', 'n', 'cancel']:
            return jsonify({"message": "Request cancelled"}), 200
        else:
            return jsonify({"error": "Invalid confirmation response"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
