from collections import Counter

def most_common_emotion(emotion_list):
    if not emotion_list:
        return "unknown"
    return Counter(emotion_list).most_common(1)[0][0]

def print_emotion_summary(emotion_logs):
    print("[Emotion Summary]")
    for idx, log in enumerate(emotion_logs):
        print(f"{idx+1}: {log}") 