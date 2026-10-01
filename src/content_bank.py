"""Verified content bank for free, API-less production (since 2026-10-01).

Emre wants the channel to run without paid API calls. A local model was
tested and invented references, which is unacceptable here. So every entry
below was written by Claude in a subscription session and limited to
references that are well established:

- Qur'an verses with surah:ayah
- hadith only from Sahih al-Bukhari / Sahih Muslim / Jami' at-Tirmidhi with
  their common (sunnah.com) numbering
- history only with widely documented facts

Translations are paraphrased meaning, not a quoted published translation.
The weekly channel agent adds new entries (rules in
~/Projects/kanal-waechter/AGENTEN.md). Titles must never repeat; the history
check in local_content.py blocks any title that was already posted.
"""

BANK = [
    # ------------------------------------------------------------------ dua
    {
        "content_type": "dua", "title": "The Dua to Keep Your Heart From Drifting",
        "hook": "Even guided hearts ask for this",
        "body": "In Surah Al Imran, people of deep knowledge ask Allah not to let their hearts drift after He has guided them. They do not assume guidance is permanent by their own strength. They ask for mercy from Allah, because He is the Giver. If your faith feels strong today, thank Allah for it and ask Him to keep it that way.",
        "translation": "Our Lord, do not let our hearts deviate after You have guided us, and grant us mercy from Yourself. Indeed, You are the Bestower.",
        "source": "Qur'an 3:8", "tags": ["dua", "quran", "guidance", "heart"],
    },
    {
        "content_type": "dua", "title": "The Dua for a Family That Brings You Peace",
        "hook": "Ask for this when you think about your family",
        "body": "The servants of the Most Merciful ask Allah for spouses and children who are a comfort to their eyes. The Arabic image is a cool, calm eye, the opposite of worry and tears. They also ask to be an example for the righteous. It is a beautiful dua for anyone who is married, hoping to marry, or raising children.",
        "translation": "Our Lord, grant us from our spouses and children comfort to our eyes, and make us an example for the righteous.",
        "source": "Qur'an 25:74", "tags": ["dua", "family", "marriage", "children"],
    },
    {
        "content_type": "dua", "title": "The Dua to Say for Your Parents Every Day",
        "hook": "Allah Himself taught us how to pray for our parents",
        "body": "In Surah Al-Isra, Allah commands kindness to parents and then gives us the words to pray for them. We ask Him to have mercy on them, just as they cared for us when we were small. Whether your parents are alive or have passed away, this dua is a gift you can give them every single day.",
        "translation": "My Lord, have mercy on them as they raised me when I was small.",
        "source": "Qur'an 17:24", "tags": ["dua", "parents", "mercy", "family"],
    },
    {
        "content_type": "dua", "title": "The First Dua of Repentance in History",
        "hook": "This was the first repentance of humanity",
        "body": "After Adam and Hawwa ate from the tree, they did not make excuses. They turned to Allah with honest words: they admitted they had wronged themselves and asked for forgiveness and mercy. Allah accepted their repentance. This dua shows that admitting a mistake is not weakness. It is the beginning of coming back to Allah.",
        "translation": "Our Lord, we have wronged ourselves. If You do not forgive us and have mercy on us, we will surely be among the losers.",
        "source": "Qur'an 7:23", "tags": ["dua", "repentance", "adam", "forgiveness"],
    },
    {
        "content_type": "dua", "title": "The Dua to Say When You Need Mercy",
        "hook": "The last verse of a surah ends with this dua",
        "body": "Surah Al-Mu'minun ends with a short instruction: ask your Lord to forgive and to have mercy, because He is the best of those who show mercy. No long speech is needed. When you feel you have fallen short, these few words can open the door. Say them slowly and mean every word.",
        "translation": "My Lord, forgive and have mercy, for You are the best of those who show mercy.",
        "source": "Qur'an 23:118", "tags": ["dua", "mercy", "forgiveness", "quran"],
    },
    {
        "content_type": "dua", "title": "The Dua a Small Army Made Before Facing Goliath",
        "hook": "They were few, and the enemy was huge",
        "body": "When Talut's small army faced Jalut, known in English as Goliath, many expected defeat. The believers among them asked Allah for patience, firm feet, and victory. Then young Dawud defeated Jalut. Their dua is perfect for any moment that feels bigger than you: an exam, a hard conversation, or a fear you must face.",
        "translation": "Our Lord, pour patience upon us, make our feet firm, and give us victory.",
        "source": "Qur'an 2:250-251", "tags": ["dua", "courage", "dawud", "patience"],
    },
    {
        "content_type": "dua", "title": "The Dua of the Young Men in the Cave",
        "hook": "They had nothing left but this dua",
        "body": "The young men of the cave left everything behind to protect their faith. When they reached the cave, they did not ask for wealth or safety first. They asked Allah for mercy from Himself and for right guidance in their situation. Allah protected them in a way no one could have planned. Say this dua when you feel lost.",
        "translation": "Our Lord, grant us mercy from Yourself and guide us rightly in our affair.",
        "source": "Qur'an 18:10", "tags": ["dua", "cave", "kahf", "guidance"],
    },
    {
        "content_type": "dua", "title": "The Dua Sulayman Made After Hearing an Ant",
        "hook": "A king smiled at an ant, then made this dua",
        "body": "Prophet Sulayman heard an ant warning the other ants to get out of the way of his army. He smiled, and instead of feeling proud of his power, he turned to Allah. He asked for help to be grateful for the blessings given to him and his parents, and to do good that pleases Allah. Gratitude is a skill we ask Allah to teach us.",
        "translation": "My Lord, inspire me to be grateful for Your favor upon me and my parents, and to do righteous deeds that please You.",
        "source": "Qur'an 27:19", "tags": ["dua", "gratitude", "sulayman", "quran"],
    },
    {
        "content_type": "dua", "title": "The Dua Ibrahim Made While Building the Kaaba",
        "hook": "They built the House of Allah and still asked this",
        "body": "Ibrahim and his son Isma'il raised the foundations of the Kaaba with their own hands. While doing one of the greatest deeds in history, they did not feel they had earned anything. They simply asked Allah to accept it from them. Before you finish any good deed, a prayer, a donation, or a kind act, ask Allah to accept it.",
        "translation": "Our Lord, accept this from us. Indeed, You are the All-Hearing, the All-Knowing.",
        "source": "Qur'an 2:127", "tags": ["dua", "ibrahim", "kaaba", "acceptance"],
    },
    {
        "content_type": "dua", "title": "The Dua to Say When You Hand Everything to Allah",
        "hook": "Ibrahim and his followers said this together",
        "body": "In Surah Al-Mumtahanah, Ibrahim and those with him declare where their trust lies. They tell Allah that they rely on Him, turn back to Him, and know that everything returns to Him. When you have done everything you can and the outcome is out of your hands, these words help you let go with peace.",
        "translation": "Our Lord, upon You we rely, to You we turn, and to You is the final return.",
        "source": "Qur'an 60:4", "tags": ["dua", "tawakkul", "trust", "ibrahim"],
    },
    {
        "content_type": "dua", "title": "The Dua Ibrahim Made for His Future Children",
        "hook": "He prayed for people he would never meet",
        "body": "Ibrahim asked Allah to make him someone who establishes prayer, and to do the same for his descendants. Then he asked forgiveness for himself, his parents, and all believers on the Day of Judgment. His dua reached far beyond his own life. You can pray today for children and grandchildren you have not even met yet.",
        "translation": "My Lord, make me one who establishes prayer, and from my descendants too. Our Lord, accept my supplication. Our Lord, forgive me, my parents, and the believers on the Day the account is established.",
        "source": "Qur'an 14:40-41", "tags": ["dua", "ibrahim", "children", "prayer"],
    },
    # ---------------------------------------------------------------- quran
    {
        "content_type": "quran", "title": "The Verse for Anyone Who Thinks It Is Too Late",
        "hook": "No sin is bigger than this verse",
        "body": "In Surah Az-Zumar, Allah addresses those who have wronged themselves and tells them not to despair of His mercy. He forgives all sins for the one who returns to Him. Scholars call it one of the most hopeful verses in the Qur'an. If you feel too far gone, this verse was written for exactly that feeling.",
        "translation": "Say: O My servants who have wronged themselves, do not despair of the mercy of Allah. Indeed, Allah forgives all sins.",
        "source": "Qur'an 39:53", "tags": ["quran", "mercy", "repentance", "hope"],
    },
    {
        "content_type": "quran", "title": "Closer to You Than Your Own Jugular Vein",
        "hook": "The Qur'an uses this image for Allah's closeness",
        "body": "In Surah Qaf, Allah says that He created the human being, knows what his own soul whispers to him, and is closer to him than his jugular vein. Your thoughts, worries, and hopes are fully known. Nothing you feel is hidden or unnoticed. That can be a warning, but it is also a deep comfort.",
        "translation": "We created man and know what his soul whispers to him, and We are closer to him than his jugular vein.",
        "source": "Qur'an 50:16", "tags": ["quran", "nearness", "knowledge", "reminder"],
    },
    {
        "content_type": "quran", "title": "Why Allah Made Us Different Nations",
        "hook": "This verse ends every argument about superiority",
        "body": "In Surah Al-Hujurat, Allah tells humanity that He created us from a male and a female and made us nations and tribes so that we may know one another. Then comes the measure that matters: the most noble in the sight of Allah is the most righteous. Not skin, not family name, not country. Character and taqwa.",
        "translation": "O mankind, We created you from a male and a female and made you nations and tribes so that you may know one another. The most noble of you to Allah is the most righteous.",
        "source": "Qur'an 49:13", "tags": ["quran", "equality", "unity", "taqwa"],
    },
    {
        "content_type": "quran", "title": "Maybe You Hate Something That Is Good for You",
        "hook": "What you wanted might have hurt you",
        "body": "In Surah Al-Baqarah 2:216, Allah reminds us that we may dislike something while it is good for us, and love something while it is bad for us. Allah knows, and we do not. This verse does not ask you to pretend a loss does not hurt. It asks you to trust that your view of the story is not the whole story.",
        "translation": "Perhaps you dislike something while it is good for you, and perhaps you love something while it is bad for you. Allah knows, and you do not know.",
        "source": "Qur'an 2:216", "tags": ["quran", "qadr", "trust", "patience"],
    },
    {
        "content_type": "quran", "title": "Saving One Life Is Like Saving All of Humanity",
        "hook": "One life carries the weight of everyone",
        "body": "In Surah Al-Ma'idah, the Qur'an recalls a decree given to the Children of Israel: whoever kills a soul unjustly, it is as if he has killed all of mankind, and whoever saves one life, it is as if he has saved all of mankind. Every single human life carries enormous value. Helping one person is never a small thing in the sight of Allah.",
        "translation": "Whoever saves one life, it is as if he has saved all of mankind.",
        "source": "Qur'an 5:32", "tags": ["quran", "life", "mercy", "humanity"],
    },
    {
        "content_type": "quran", "title": "Seek Help Through Patience and Prayer",
        "hook": "The Qur'an gives two tools for hard days",
        "body": "In Surah Al-Baqarah 2:153, Allah tells the believers to seek help through patience and prayer, and says that He is with the patient. Patience keeps you steady while you wait. Prayer connects you to the One who can change everything. Use both when life gets heavy.",
        "translation": "O you who believe, seek help through patience and prayer. Indeed, Allah is with the patient.",
        "source": "Qur'an 2:153", "tags": ["quran", "patience", "salah", "hardship"],
    },
    # --------------------------------------------------------------- hadith
    {
        "content_type": "hadith", "title": "Small Deeds Allah Loves the Most",
        "hook": "Allah loves this more than big bursts of effort",
        "body": "The Prophet taught that the deeds most beloved to Allah are those done consistently, even if they are small. A few verses every day, a short dhikr after each prayer, a small regular charity. Big bursts of motivation fade. Small habits stay. Choose one good deed you can keep doing for the rest of your life.",
        "translation": "The most beloved deeds to Allah are those done consistently, even if they are small.",
        "source": "Sahih al-Bukhari 6464; Sahih Muslim 783", "tags": ["hadith", "consistency", "habits", "deeds"],
    },
    {
        "content_type": "hadith", "title": "Allah Looks at Your Heart, Not Your Looks",
        "hook": "This is what Allah actually looks at",
        "body": "The Prophet said that Allah does not look at your appearance or your wealth, but He looks at your hearts and your deeds. In a world that judges people by photos, clothes, and bank accounts, this hadith resets the scale. What matters is what is inside you and what you do with it.",
        "translation": "Allah does not look at your forms or your wealth, but He looks at your hearts and your deeds.",
        "source": "Sahih Muslim 2564", "tags": ["hadith", "heart", "sincerity", "character"],
    },
    {
        "content_type": "hadith", "title": "Make Things Easy, Not Difficult",
        "hook": "The Prophet gave this advice to people he sent out",
        "body": "The Prophet instructed: make things easy and do not make them difficult, give good news and do not drive people away. This is guidance for teachers, parents, leaders, and anyone who talks about faith. People come closer through gentleness and hope, not through harshness. Make the path to Allah feel like a door, not a wall.",
        "translation": "Make things easy and do not make them difficult. Give good news and do not drive people away.",
        "source": "Sahih al-Bukhari 69; Sahih Muslim 1734", "tags": ["hadith", "ease", "dawah", "gentleness"],
    },
    {
        "content_type": "hadith", "title": "Relieve Someone's Hardship and Allah Relieves Yours",
        "hook": "Your help to others comes back to you",
        "body": "The Prophet taught that whoever relieves a believer of a hardship in this world, Allah will relieve him of a hardship on the Day of Resurrection. Whoever makes things easy for someone in difficulty, Allah makes things easy for him. And Allah helps His servant as long as the servant helps his brother.",
        "translation": "Allah helps His servant as long as the servant helps his brother.",
        "source": "Sahih Muslim 2699", "tags": ["hadith", "helping", "kindness", "community"],
    },
    {
        "content_type": "hadith", "title": "Gentleness Makes Everything Beautiful",
        "hook": "This one quality improves everything it touches",
        "body": "The Prophet said that gentleness is not found in anything except that it beautifies it, and it is not removed from anything except that it makes it ugly. A correction said gently, a reminder said kindly, a no said with respect. The same words can heal or hurt depending on how they are said.",
        "translation": "Gentleness is not in anything except that it beautifies it, and it is not removed from anything except that it disfigures it.",
        "source": "Sahih Muslim 2594", "tags": ["hadith", "gentleness", "manners", "character"],
    },
    {
        "content_type": "hadith", "title": "The Best of You According to the Prophet",
        "hook": "The Prophet named who the best people are",
        "body": "The Prophet said that the best among you are those who learn the Qur'an and teach it. Teaching does not require being a scholar. Helping a child learn Al-Fatiha, correcting a friend's recitation kindly, or sharing a verse with its meaning all count. Learn a little, then pass it on.",
        "translation": "The best of you are those who learn the Qur'an and teach it.",
        "source": "Sahih al-Bukhari 5027", "tags": ["hadith", "quran", "teaching", "learning"],
    },
    {
        "content_type": "hadith", "title": "Purity Is Half of Faith",
        "hook": "Half of faith starts with this",
        "body": "The Prophet said that purity is half of faith. It begins with physical cleanliness: wudu, a clean body, clean clothes, and a clean place of prayer. But it also points to a pure heart free from envy and arrogance. Every time you make wudu, remember you are preparing both your body and your heart to meet Allah.",
        "translation": "Purity is half of faith.",
        "source": "Sahih Muslim 223", "tags": ["hadith", "purity", "wudu", "faith"],
    },
    # -------------------------------------------------------- prophet_story
    {
        "content_type": "prophet_story", "title": "Zakariya Prayed for a Child in Old Age",
        "hook": "Everyone said it was impossible",
        "body": "Zakariya was old, his hair was white, and his wife was unable to have children. Still, he called on Allah quietly and said he had never been disappointed in his prayers to Him. Allah gave him the good news of a son named Yahya, a name given to no one before. Never decide on Allah's behalf that a dua is impossible.",
        "translation": "I have never been disappointed in my supplication to You, my Lord.",
        "source": "Qur'an 19:2-7", "tags": ["prophet story", "zakariya", "dua", "hope"],
    },
    {
        "content_type": "prophet_story", "title": "Musa and Khidr: The Boat, the Boy and the Wall",
        "hook": "Every strange event had a hidden reason",
        "body": "Musa traveled with a servant of Allah known as Khidr, who did three things that seemed wrong: he damaged a boat, he took a boy's life, and he rebuilt a wall without payment. Later he explained the hidden wisdom behind each one. The boat was saved from a king who seized ships, and the wall protected orphans' treasure. Some things only make sense later.",
        "translation": "This is the interpretation of that about which you could not have patience.",
        "source": "Qur'an 18:60-82", "tags": ["prophet story", "musa", "khidr", "wisdom"],
    },
    {
        "content_type": "prophet_story", "title": "Maryam Alone Under a Palm Tree",
        "hook": "In her hardest moment, food fell from a tree",
        "body": "When Maryam was about to give birth to 'Isa, she was alone and in pain beside the trunk of a palm tree. She wished she had been forgotten. Then she was told not to grieve: Allah had placed a stream beneath her and told her to shake the palm tree so fresh dates would fall. Allah's help came with a small action from her side.",
        "translation": "Shake the trunk of the palm tree toward you; fresh ripe dates will fall upon you.",
        "source": "Qur'an 19:22-26", "tags": ["prophet story", "maryam", "isa", "hope"],
    },
    {
        "content_type": "prophet_story", "title": "Yaqub Lost Two Sons and Still Said This",
        "hook": "Grief did not break his trust in Allah",
        "body": "Prophet Yaqub lost Yusuf, and years later his youngest son was held in Egypt too. He wept until his eyes turned white from grief. Yet he said that he only complains of his sorrow to Allah, and he told his sons never to despair of Allah's relief. Crying is not a lack of faith. Taking your grief to Allah is faith.",
        "translation": "I only complain of my suffering and my grief to Allah.",
        "source": "Qur'an 12:84-87", "tags": ["prophet story", "yaqub", "grief", "patience"],
    },
    # -------------------------------------------------------- islamic_story
    {
        "content_type": "islamic_story", "title": "Do Not Grieve, Allah Is With Us",
        "hook": "The enemy stood right at the entrance of the cave",
        "body": "During the Hijra, the Prophet and Abu Bakr hid in the cave of Thawr while their pursuers searched nearby. Abu Bakr was afraid, not for himself, but for the Prophet. The Prophet calmed him with words the Qur'an preserved forever: do not grieve, indeed Allah is with us. They left safely and reached Madinah.",
        "translation": "Do not grieve; indeed, Allah is with us.",
        "source": "Qur'an 9:40; Sahih al-Bukhari 3653", "tags": ["islamic story", "hijra", "abu bakr", "trust"],
    },
    {
        "content_type": "islamic_story", "title": "The Prophet Let His Title Be Erased From a Treaty",
        "hook": "He agreed to remove his own title",
        "body": "At Hudaybiyyah, the Muslims signed a treaty with Quraysh. The Quraysh negotiator refused the words Messenger of Allah in the document. The Prophet agreed to write Muhammad son of Abdullah instead, even though his companions were upset. The treaty looked like a loss, but it brought peace, and Islam spread faster in the years that followed.",
        "translation": "",
        "source": "Sahih al-Bukhari 2731-2732", "tags": ["islamic story", "hudaybiyyah", "seerah", "wisdom"],
    },
    # --------------------------------------------------------- did_you_know
    {
        "content_type": "did_you_know", "title": "The Surgeon Who Designed 200 Surgical Tools in 1000 AD",
        "hook": "Modern surgery owes a lot to this man",
        "body": "Abu al-Qasim al-Zahrawi, known in Europe as Abulcasis, lived in Cordoba around the year 1000. He wrote a huge medical encyclopedia called Al-Tasrif. Its surgery section described and illustrated around two hundred surgical instruments. It was translated into Latin and used in Europe for centuries. Seeking knowledge to heal people is an act of worship.",
        "translation": "",
        "source": "Encyclopaedia Britannica: Abu al-Qasim al-Zahrawi", "tags": ["did you know", "islamic history", "medicine", "andalus"],
    },
    {
        "content_type": "did_you_know", "title": "Europe Studied Medicine From This Muslim Book for Centuries",
        "hook": "This book was a medical textbook for 600 years",
        "body": "Ibn Sina, known in the West as Avicenna, completed The Canon of Medicine in the early 11th century. It organized the medical knowledge of his time into five books. After its Latin translation, European universities used it as a main medical textbook for centuries, into the 1600s. Curiosity about Allah's creation built entire sciences.",
        "translation": "",
        "source": "Encyclopaedia Britannica: Avicenna, The Canon of Medicine", "tags": ["did you know", "ibn sina", "medicine", "islamic history"],
    },
    {
        "content_type": "did_you_know", "title": "The Muslim Traveler Who Covered 117,000 Kilometers",
        "hook": "He traveled further than Marco Polo",
        "body": "In 1325, a young man from Tangier named Ibn Battuta set out to perform Hajj. He did not come home for about 24 years. Over almost three decades of travel he visited North Africa, the Middle East, India, China, and West Africa, covering an estimated 117,000 kilometers. His journey began with a single intention: to visit the House of Allah.",
        "translation": "",
        "source": "Encyclopaedia Britannica: Ibn Battuta", "tags": ["did you know", "ibn battuta", "travel", "hajj"],
    },
    {
        "content_type": "did_you_know", "title": "The Scholar Who Measured the Earth From a Mountain",
        "hook": "He measured the Earth with a mountain and geometry",
        "body": "Around the year 1025, the scholar al-Biruni used a clever method: he measured the height of a mountain and the angle down to the horizon from its peak. With geometry, he calculated the radius of the Earth. His result was remarkably close to the modern value of about 6,371 kilometers. Reflection on creation is something the Qur'an repeatedly encourages.",
        "translation": "",
        "source": "Encyclopaedia Britannica: al-Biruni", "tags": ["did you know", "al biruni", "science", "islamic history"],
    },
    {
        "content_type": "did_you_know", "title": "The Map Made in Sicily That Put South at the Top",
        "hook": "This famous world map is upside down to us",
        "body": "In 1154, the Muslim geographer al-Idrisi completed a world map and book for King Roger II of Sicily. It was one of the most accurate world maps of the medieval period. Like many maps from the Muslim world, it placed south at the top. Al-Idrisi gathered reports from travelers and merchants for years to make it.",
        "translation": "",
        "source": "Encyclopaedia Britannica: al-Idrisi", "tags": ["did you know", "al idrisi", "maps", "geography"],
    },
    # --------------------------------------------------------------- akhlaq
    {
        "content_type": "akhlaq", "title": "The Qur'an Compares Backbiting to This",
        "hook": "The Qur'an uses a shocking image for gossip",
        "body": "In Surah Al-Hujurat, Allah forbids spying and backbiting, and then asks: would any of you like to eat the flesh of his dead brother? You would hate it. The image is meant to shock. Talking about someone behind their back, even if it is true, tears at a person who cannot defend themselves. Guard your tongue in every conversation.",
        "translation": "Do not spy and do not backbite one another. Would one of you like to eat the flesh of his dead brother? You would detest it.",
        "source": "Qur'an 49:12", "tags": ["akhlaq", "backbiting", "tongue", "manners"],
    },
    {
        "content_type": "akhlaq", "title": "How the Servants of the Most Merciful Walk",
        "hook": "The Qur'an describes how they walk and talk",
        "body": "Surah Al-Furqan describes the servants of the Most Merciful. They walk on the earth humbly, and when ignorant people insult them, they answer with words of peace. They do not need to win every argument. Humility in how you move and calm in how you reply are signs of a heart connected to Allah.",
        "translation": "The servants of the Most Merciful are those who walk upon the earth humbly, and when the ignorant address them, they say words of peace.",
        "source": "Qur'an 25:63", "tags": ["akhlaq", "humility", "manners", "quran"],
    },
    {
        "content_type": "akhlaq", "title": "Luqman's Advice to His Son About Arrogance",
        "hook": "A father's advice preserved in the Qur'an",
        "body": "Luqman advised his son not to turn his cheek away from people in arrogance and not to walk proudly on the earth, because Allah does not love the arrogant and boastful. He told him to be moderate in his pace and to lower his voice. Simple advice about everyday behavior, preserved forever in the Qur'an.",
        "translation": "Do not turn your cheek away from people in arrogance, and do not walk proudly on the earth. Be moderate in your pace and lower your voice.",
        "source": "Qur'an 31:18-19", "tags": ["akhlaq", "luqman", "arrogance", "parenting"],
    },
    {
        "content_type": "akhlaq", "title": "Stand for Justice Even Against Yourself",
        "hook": "This verse asks for justice even against yourself",
        "body": "In Surah An-Nisa, Allah commands the believers to stand firmly for justice as witnesses for Allah, even if it is against themselves, their parents, or their relatives, rich or poor. It is easy to be fair when fairness helps us. The Qur'an asks for honesty exactly when it costs us something.",
        "translation": "O you who believe, stand firmly for justice as witnesses for Allah, even if it is against yourselves, your parents, or your relatives.",
        "source": "Qur'an 4:135", "tags": ["akhlaq", "justice", "honesty", "quran"],
    },
    {
        "content_type": "akhlaq", "title": "Why People Gathered Around the Prophet",
        "hook": "The Qur'an names the reason people stayed close to him",
        "body": "In Surah Al Imran, Allah tells the Prophet that it was by mercy from Allah that he was gentle with people, and if he had been harsh and hard-hearted, they would have scattered from around him. Then he is told to pardon them and consult them. Kindness keeps people close. Harshness pushes them away, even from the truth.",
        "translation": "By mercy from Allah you were gentle with them. Had you been harsh and hard-hearted, they would have dispersed from around you.",
        "source": "Qur'an 3:159", "tags": ["akhlaq", "gentleness", "prophet", "leadership"],
    },
]
