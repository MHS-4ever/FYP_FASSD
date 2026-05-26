# Forensic Voice Recording — Files & Scripts

Controlled audio samples and read-aloud scripts for an audio authenticity research project.

---

## File names

| Category | File |
|----------|------|
| Human — clean | `human_001_clean.wav` |
| Human — replay | `human_001_replay_laptop_mobile.wav` |
| Human — mixer | `human_001_mixer_processed.wav` |
| Human — fabricated | `human_001_fabricated.wav` |
| AI — direct | `ai_001_direct.wav` |
| AI — replay | `ai_001_replay_laptop_mobile.wav` |
| AI — mixer | `ai_001_mixer_processed.wav` |
| AI — fabricated | `ai_001_fabricated.wav` |

**Naming pattern:** `{source}_{id}_{condition}.wav`

- **source:** `human` or `ai`
- **condition:** `clean`, `replay_laptop_mobile`, `mixer_processed`, or `fabricated`

---

## Script 1 — English

### Paragraph 1

This is a controlled forensic voice recording created for an audio authenticity research project. I am speaking in a normal and natural voice, without acting, shouting, whispering, or changing my accent on purpose. The purpose of this recording is to help test whether a system can understand the difference between clean human speech, replayed speech, processed speech, and artificially generated speech. I will try to speak clearly and consistently, but still naturally, because real-world recordings are never perfectly identical. Sometimes a person pauses, changes speed slightly, or emphasizes certain words differently, and those small differences are normal in human speech.

### Paragraph 2

In real life, audio can be affected by many things. A person may record their voice on a mobile phone, a laptop microphone, or a headset. The recording may happen in a quiet room, a classroom, an office, or a place with a fan running in the background. Later, the same audio may be played through a speaker, sent through a messaging app, compressed by a platform, or modified using software. These changes can introduce background noise, echo, microphone effects, speaker distortion, and other acoustic patterns. A forensic voice system should not simply say real or fake without explaining why the audio seems trustworthy, suspicious, replayed, processed, or artificial.

### Paragraph 3

This sample is part of a controlled dataset, so the same or similar text may be spoken by different speakers. That makes the comparison more reliable because the system can focus on voice quality, recording conditions, and manipulation artifacts instead of being confused by completely different content. The final goal of this project is to build a forensic voice authenticity analyzer that can review an audio file and produce a useful report. The report should explain whether the speech sounds human or artificial, whether the recording appears clean or manipulated, and whether any specific part of the audio needs closer review.

---

## Script 2 — Urdu / Roman Urdu

### Paragraph 1

Yeh aik controlled forensic voice recording hai jo audio authenticity research project ke liye banai ja rahi hai. Main apni normal aur natural awaz mein bol raha hoon, bina acting ke, bina cheekhne ke, bina dheemi awaz banaye, aur bina jaan boojh kar accent change kiye. Is recording ka maqsad yeh check karna hai ke system clean human voice, replayed voice, processed voice, aur AI generated voice ke darmiyan farq samajh sakta hai ya nahi. Main koshish karunga ke meri awaz clear ho, lekin bilkul natural bhi rahe, kyun ke real life recordings mein choti moti pauses, speed changes, aur lafzon ka emphasis normal hota hai.

### Paragraph 2

Asal zindagi mein audio bohat si cheezon se affect ho sakti hai. Kabhi voice mobile phone se record hoti hai, kabhi laptop mic se, kabhi headset se, aur kabhi kisi room mein background fan ya halka noise hota hai. Baad mein wahi audio speaker par play ho sakti hai, WhatsApp ya kisi aur app se send ho sakti hai, compress ho sakti hai, ya kisi software se edit bhi ho sakti hai. In sab cheezon ki wajah se audio mein echo, background noise, microphone effect, speaker distortion, aur channel artifacts aa sakte hain. Is liye forensic system ko sirf real ya fake nahi kehna chahiye, balki yeh bhi explain karna chahiye ke audio clean hai, suspicious hai, replayed hai, processed hai, ya artificial lag rahi hai.

### Paragraph 3

Yeh sample aik controlled dataset ka hissa hai, is liye mumkin hai ke different speakers same ya similar text read karein. Is se comparison zyada reliable hota hai, kyun ke system content ke bajaye voice quality, recording condition, aur manipulation artifacts par focus kar sakta hai. Is project ka final goal aik forensic voice authenticity analyzer banana hai jo audio file ko analyze kar ke useful report de sake. Report mein yeh bataya jana chahiye ke speech human lag rahi hai ya AI generated, recording original aur clean hai ya manipulated, aur kya audio ke kisi specific part ko manual review ki zaroorat hai.

---

## Script 3 — English + Urdu (mixed)

### Paragraph 1

This is a controlled voice sample for a forensic audio detection project. Main apni normal speaking style mein baat kar raha hoon, without trying to sound different or dramatic. The goal of this recording is to help test whether the system can detect clean human speech, replayed audio, processed audio, and AI-generated speech. Real human speech usually has natural variation. Kabhi speaker thora pause leta hai, kabhi sentence ka flow change hota hai, aur kabhi kuch words par natural emphasis aa jata hai. These small variations are normal and should not automatically be treated as fake or suspicious.

### Paragraph 2

In practical situations, audio ka source aur recording condition bohat important hoti hai. A voice can be recorded directly on a phone, played through a laptop speaker, re-recorded with another mobile, or sent through WhatsApp where compression changes the signal. Isi tarah, kisi audio ko mixer, equalizer, noise reduction, reverb, ya pitch effect ke through process bhi kiya ja sakta hai. A forensic voice system should understand that processed human audio is not always AI fake. Kabhi audio human-origin hoti hai lekin replayed ya channel-processed hoti hai. That is why the system should give a layered result instead of only saying real or fake.

### Paragraph 3

This dataset is being collected carefully so that different speakers can read similar content under controlled conditions. Is se humein compare karne mein madad milegi ke clean recording, replayed recording, AI voice, aur edited audio mein model ka behavior kaisa hai. The final product should be more than a simple classifier. It should become a forensic voice authenticity analyzer that can explain origin, manipulation risk, suspicious segments, and confidence level. Agar koi audio mostly real ho lekin beech mein AI-generated part insert kiya gaya ho, then the system should highlight that suspicious region instead of giving only one whole-file decision.
