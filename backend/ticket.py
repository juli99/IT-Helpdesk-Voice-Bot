from datetime import datetime


def generate_ticket(session: dict) -> dict:
    return {
        'ticket_id':             f"TKT-{datetime.now():%Y%m%d%H%M%S}",
        'timestamp':             datetime.now().isoformat(),
        'caller_id':             session.get('caller_id', 'Unknown'),
        'tier':                  session.get('tier'),
        'intent':                session.get('intent'),
        'raw_transcript':        session.get('raw_transcript'),
        'corrected_transcript':  session.get('corrected_transcript'),
        'asr_corrections':       session.get('corrections', []),
        'steps_attempted':       session.get('steps_taken', []),
        'outcome':               session.get('outcome'),
        'escalation_reason':     session.get('escalation_reason')
    }
