"""POV day stories for Muslim World (format since 15.11.2026).

Modelled on the "POV: you wake up in <city>" TikToks (e.g. @wander_frame_):
first-person camera (only your own hands / phone / cup are visible, no faces),
soft stylised 3D miniature look, a quiet inner-monologue voice, a clock +
date/place in the top-left corner and small fact chips.

Rules (channel policy, same as the story bank):
  * Facts in chips must be well established; hadith only from Bukhari/Muslim/
    the Sunan with sunnah.com numbering, Qur'an per Sahih International.
    When unsure: leave the number out, never guess.
  * No faces of people (it's POV), never prophets/Sahaba depicted, no Kaaba
    interior, nothing staged as a real person.
  * ~10-14 scenes, one short spoken line each, 45-65 s.

Schema:
  id, title, hook (on-screen POV line in scene 1), date (shown under the clock),
  place, scenes: [{"time": "05:12", "shot": image description,
                   "line": spoken inner monologue,
                   "chip": {"title": ..., "sub": ...} (optional)}],
  tags
"""

POVS = [
    {
        "id": "pov-madinah-day",
        "title": "POV: You Wake Up in Madinah 🕌",
        "hook": "POV: You wake up in Madinah.",
        "date": "Fri, 20 Nov",
        "place": "Madinah",
        "scenes": [
            {"time": "04:48", "shot": "first-person view from a hotel bed at night, a phone in your hand showing an alarm clock 04:48, a window with the green dome and minarets of a huge mosque glowing in the distance",
             "line": "Mm… Madinah. I almost forgot."},
            {"time": "04:55", "shot": "first-person view out of a hotel window before dawn, the Prophet's Mosque with white minarets and a green dome lit up, streets with people walking towards it",
             "line": "The whole city is already walking to the masjid.",
             "chip": {"title": "Al-Masjid an-Nabawi", "sub": "first built in 622 CE, year 1 of the Hijrah"}},
            {"time": "05:10", "shot": "first-person view walking across a huge empty white marble courtyard at dawn, looking ahead at folded giant white umbrella canopies and minarets, soft blue light, no hands visible",
             "line": "The marble is cold under my feet."},
            {"time": "05:20", "shot": "first-person view sitting on a red carpet inside a vast mosque hall, looking ahead along endless white columns and golden chandeliers, rows of worshippers far ahead seen from behind, no hands visible",
             "line": "One prayer here… is worth more than a thousand elsewhere.",
             "chip": {"title": "Better than 1,000 prayers", "sub": "except al-Masjid al-Haram · Sahih al-Bukhari 1190"}},
            {"time": "07:30", "shot": "first-person view at a date market stall, your hand holding a small dark wrinkled ajwa date, wooden crates full of different dates, warm morning sun",
             "line": "Ajwa. Seven of them, in the morning.",
             "chip": {"title": "Ajwa dates", "sub": "the Sunnah of seven in the morning · Sahih al-Bukhari 5445"}},
            {"time": "09:00", "shot": "first-person view from the back seat of a taxi, the white Quba mosque with four minarets appearing through the windshield, palm trees",
             "line": "Next stop. Quba.",
             "chip": {"title": "Masjid Quba", "sub": "the first mosque built in Islam"}},
            {"time": "09:20", "shot": "first-person view standing in front of the bright white Quba mosque entrance, your hands still wet from wudu, morning sun, palm trees",
             "line": "Wudu at home, two rak'ah here… like the reward of an umrah.",
             "chip": {"title": "Prayer in Quba", "sub": "reward like an umrah · Sunan Ibn Majah 1412"}},
            {"time": "11:40", "shot": "first-person view looking up at a large reddish brown rocky mountain under a clear blue sky, a small low hill in front of it",
             "line": "Uhud. It's so much bigger than I imagined.",
             "chip": {"title": "Mount Uhud", "sub": "site of the Battle of Uhud, 3 AH / 625 CE"}},
            {"time": "12:15", "shot": "first-person view of a huge mosque courtyard at noon, giant white umbrella canopies opening above, thousands of worshippers in white walking in",
             "line": "Jumu'ah. The umbrellas are opening.",
             "chip": {"title": "250 umbrellas", "sub": "open at sunrise to shade the courtyard"}},
            {"time": "14:30", "shot": "first-person view of a green carpet area between ornate white columns with green and gold decorations, soft light, your hands holding a small Quran",
             "line": "Between his house and his minbar… a garden of Paradise.",
             "chip": {"title": "Ar-Rawdah", "sub": "a garden from the gardens of Paradise · Sahih al-Bukhari 1196"}},
            {"time": "17:40", "shot": "first-person view from the courtyard at sunset, the green dome glowing gold, pink and orange sky, birds flying, your hand holding a cup of zamzam water",
             "line": "Maghrib. The sky turns pink over the green dome."},
            {"time": "21:00", "shot": "first-person view from a hotel bed at night, a phone in your hand with a message chat open, the lit minarets visible through the window",
             "line": "I know exactly who I'm sending this to."},
        ],
        "ending": {"arabic": "المدينة المنورة", "word": "Al-Madinah al-Munawwarah",
                   "reminder": "Between my house and my pulpit there is a garden from the gardens of Paradise.",
                   "source": "Sahih al-Bukhari 1196"},
        "tags": ["madinah", "pov", "islam", "muslim", "masjid nabawi"],
    },
]


def all_povs() -> list[dict]:
    return list(POVS)
