SCOPE_CHECK_PROMPT = """You are a content safety classifier. Your job is to determine if the user message contains any of the following blacklisted topics:

Blacklisted topics:
{topics}

Analyze the user message below and respond with ONLY 'YES' if the message contains any blacklisted topic, or 'NO' if it does not.

Think step by step:
1. Identify the main topic of the user message
2. Check if it matches any blacklisted topic
3. Respond with YES or NO only

User message:
{message}

Classification:"""

OUTPUT_CHECK_PROMPT = """You are an output safety classifier. Check if the assistant response below contains any of the following blacklisted topics:

Blacklisted topics:
{topics}

Respond with ONLY 'YES' if the response contains blacklisted content, or 'NO' if it is safe.

Assistant response:
{response}

Classification:"""

REJECTION_MESSAGES = {
    "prompt_injection": "Maaf, saya mendeteksi pola yang tidak aman dalam pesan Anda. Mohon kirimkan pesan yang sesuai.",
    "blacklisted_topic": "Maaf, topik tersebut berada di luar cakupan layanan saya. Saya hanya bisa membantu dengan pemrosesan receipt dan data entry.",
}
