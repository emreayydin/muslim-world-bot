"""Conservative, source-marked Islamic content for API-free production.

The public channel must not improvise religious references when a text API is
unavailable. These entries are intentionally small and well-known; a scheduled
run rotates them and history prevents immediate title repeats.
"""
from copy import deepcopy


VISUALS = [
    "serene sunrise over mountains, cinematic, no people, no text",
    "Islamic geometric pattern with soft golden light, no people, no text",
    "quiet ocean under a starry sky, reverent cinematic style, no people, no text",
    "mosque architecture silhouette at dawn, no people, no text",
]


ENTRIES = [
    {
        "content_type": "quran", "title": "Allah Does Not Burden a Soul Beyond Its Capacity",
        "hook": "Your hardship is not beyond Allah's knowledge",
        "body": "The Qur'an reminds us that Allah does not burden a soul beyond what it can bear. This is not a promise that life will feel easy. It is a reminder that your struggle is seen, and that you are not asked to carry more than your capacity. When a difficult day comes, take the next faithful step instead of demanding that you solve everything at once.",
        "translation": "Allah does not burden a soul beyond what it can bear.",
        "source": "Qur'an 2:286", "tags": ["quran", "patience", "faith", "islamic reminder"],
    },
    {
        "content_type": "quran", "title": "With Hardship Comes Ease",
        "hook": "The Qur'an repeats this promise for a reason",
        "body": "Surah Ash-Sharh repeats the reminder that with hardship comes ease. The repetition teaches us to look for openings even while a problem is still present. Ease may arrive as patience, a helpful person, a clearer choice, or a new strength in your heart. Do not assume that a difficult chapter is the whole story.",
        "translation": "Indeed, with hardship comes ease.",
        "source": "Qur'an 94:5-6", "tags": ["quran", "ease", "hope", "faith"],
    },
    {
        "content_type": "quran", "title": "Where Hearts Find Real Rest",
        "hook": "The Qur'an names where the heart finds rest",
        "body": "The Qur'an says that hearts find rest in the remembrance of Allah. This does not mean that a believer never feels anxious or tired. It means remembrance gives the heart a direction when feelings become noisy. A quiet prayer, a sincere supplication, or a few mindful words can bring you back to what matters.",
        "translation": "Surely, in the remembrance of Allah do hearts find rest.",
        "source": "Qur'an 13:28", "tags": ["quran", "dhikr", "peace", "heart"],
    },
    {
        "content_type": "hadith", "title": "Strength Is More Than Physical Power",
        "hook": "The strongest believer is not defined by muscles",
        "body": "The Prophet taught that the strong believer is better and more beloved to Allah than the weak believer, while there is good in both. The hadith points to useful strength: faith, effort, courage, and the ability to keep choosing what is right. Build your body, your character, and your trust in Allah together.",
        "source": "Sahih Muslim 2664", "tags": ["hadith", "strength", "faith", "character"],
    },
    {
        "content_type": "hadith", "title": "Speak Good or Remain Silent",
        "hook": "One sentence can protect your whole day",
        "body": "The Prophet said that whoever believes in Allah and the Last Day should speak good or remain silent. This is not a command to avoid every difficult conversation. It is a filter: is this true, useful, and kind enough to say? Before sending a message or repeating a story, pause and choose words that leave less harm behind.",
        "source": "Sahih al-Bukhari 6018", "tags": ["hadith", "speech", "manners", "akhlaq"],
    },
    {
        "content_type": "hadith", "title": "Actions Begin With Intentions",
        "hook": "The same action can change with one intention",
        "body": "The first hadith in many collections teaches that actions are judged by intentions. Two people may perform the same outward action while seeking very different things. Before you begin today, renew the reason behind it: worship, benefit, responsibility, or service. A sincere intention can turn an ordinary task into an act of meaning.",
        "source": "Sahih al-Bukhari 1", "tags": ["hadith", "intention", "niyyah", "faith"],
    },
    {
        "content_type": "dua", "title": "A Dua for Good in Both Worlds",
        "hook": "This short dua asks for good everywhere",
        "body": "The Qur'an teaches a balanced supplication: ask Allah for good in this world, good in the Hereafter, and protection from the Fire. It is short enough to remember and broad enough to cover every season of life. Say it with attention, then let it guide your choices toward what benefits both your present and your future.",
        "translation": "Our Lord, give us good in this world and good in the Hereafter, and protect us from the punishment of the Fire.",
        "source": "Qur'an 2:201", "tags": ["dua", "supplication", "quran", "akhirah"],
    },
    {
        "content_type": "dua", "title": "A Dua to Increase in Knowledge",
        "hook": "The Qur'an gives students a simple dua",
        "body": "Allah teaches us a concise prayer: My Lord, increase me in knowledge. It is a reminder that learning begins with humility. Whether you are studying religion, a language, a skill, or your own mistakes, ask for beneficial knowledge and then act on what you learn. Knowledge becomes light when it changes how you live.",
        "translation": "My Lord, increase me in knowledge.",
        "source": "Qur'an 20:114", "tags": ["dua", "knowledge", "learning", "quran"],
    },
    {
        "content_type": "akhlaq", "title": "Control Anger and Choose Forgiveness",
        "hook": "The Qur'an praises people who stop before reacting",
        "body": "The Qur'an praises those who restrain anger and pardon people. Restraining anger does not mean pretending that nothing happened. It means refusing to let the first emotion choose your next action. Take space, lower your voice, and return to the situation with justice. Forgiveness can be a strength, especially when it is joined with wisdom and healthy boundaries.",
        "source": "Qur'an 3:134", "tags": ["akhlaq", "anger", "forgiveness", "character"],
    },
    {
        "content_type": "akhlaq", "title": "Do Not Ridicule Other People",
        "hook": "A joke can become injustice very quickly",
        "body": "Surah Al-Hujurat warns believers not to ridicule one another or insult each other. A joke is not harmless just because the speaker laughs. Good character notices the dignity of the person who is being discussed, especially when they are not present to answer. Before sharing a comment, ask whether it brings truth and kindness or only attention at someone else's expense.",
        "source": "Qur'an 49:11", "tags": ["akhlaq", "respect", "kindness", "quran"],
    },
    {
        "content_type": "prophet_story", "title": "Yusuf Chose Forgiveness After Power",
        "hook": "He had power over them and chose a better response",
        "body": "When Yusuf's brothers finally stood before him, he had the position to punish them. Instead, the Qur'an records his words of forgiveness and reminds them that Allah is the Most Merciful. The lesson is not that injustice should be ignored. It is that success gives you a choice: repeat the harm, or use your strength to end the cycle.",
        "source": "Qur'an 12:90-92", "tags": ["prophets", "Yusuf", "forgiveness", "quran"],
    },
    {
        "content_type": "prophet_story", "title": "Musa Found Help After a Difficult Journey",
        "hook": "After the journey, Musa made one honest prayer",
        "body": "After Musa reached Madyan, he helped two women water their flock and then withdrew into the shade. He did not pretend to have everything under control. He turned to Allah and expressed his need for whatever good could be sent to him. The story shows how service, humility, and honest supplication can open the next chapter.",
        "source": "Qur'an 28:24", "tags": ["prophets", "Musa", "dua", "trust"],
    },
    {
        "content_type": "islamic_story", "title": "Three People Were Saved by Sincere Deeds",
        "hook": "When the cave closed, only sincere deeds remained",
        "body": "A well-known hadith tells of three people trapped by a rock at the entrance of a cave. Each one called upon Allah by mentioning a sincere deed: service to parents, honesty in a difficult situation, and keeping a trust despite temptation. The rock moved after each supplication. The story teaches that private goodness can become a source of hope when no human solution is visible.",
        "source": "Sahih al-Bukhari 2272", "tags": ["story", "sincerity", "deeds", "hadith"],
    },
    {
        "content_type": "did_you_know", "title": "Ayat al-Kursi Is in Surah Al-Baqarah",
        "hook": "One of the Qur'an's most known verses has a precise place",
        "body": "Ayat al-Kursi is the name commonly used for verse 255 of Surah Al-Baqarah. The verse speaks about Allah's knowledge, authority, and care over the heavens and the earth. Knowing the reference helps us return to the Qur'an itself instead of treating a familiar phrase as a floating quotation. Read it with its surrounding context and with respect for the exact words.",
        "source": "Qur'an 2:255", "tags": ["quran", "ayatalkursi", "islamic knowledge", "reminder"],
    },
]


def _fresh(pool, avoid):
    blocked = {str(x).strip().lower() for x in (avoid or [])}
    fresh = [item for item in pool if item["title"].lower() not in blocked]
    return fresh or pool


def generate_content(content_type: str | None = None,
                     avoid: list[str] | None = None) -> dict:
    pool = [item for item in ENTRIES if not content_type or item["content_type"] == content_type]
    pool = _fresh(pool or ENTRIES, avoid)
    item = deepcopy(pool[len(avoid or []) % len(pool)])
    item.setdefault("arabic", "")
    item.setdefault("transliteration", "")
    item.setdefault("translation", "")
    item["cta"] = "Follow for a respectful daily reminder."
    item["visual_tags"] = ["nature", "sky", "mosque architecture", "Islamic geometric patterns"]
    item["image_prompts"] = list(VISUALS)
    return item


def generate_compilation(topic: str | None = None,
                         avoid: list[str] | None = None) -> dict:
    pool = _fresh(ENTRIES, avoid)
    selected = [pool[i % len(pool)] for i in range(10)]
    facts = [{
        "headline": item["title"][:40],
        "text": item["body"],
        "source": item["source"],
        "image_prompt": VISUALS[0],
    } for item in selected]
    category = topic or "Islamic reminders"
    return {
        "title": f"10 {category}: reminders for the heart",
        "topic": category,
        "intro": "These ten reminders come from well-known Qur'an verses and authentic narrations. Take one lesson with you today.",
        "hook_visual": VISUALS[0],
        "facts": facts,
        "outro": "Which reminder will you carry into today? Share it and subscribe for more careful, source-marked lessons.",
        "tags": ["Islam", "Quran", "Muslim", "Islamic reminder", "faith"],
        "visual_tags": ["nature", "sky", "mosque architecture", "Islamic geometric patterns"],
        "category": category,
    }
