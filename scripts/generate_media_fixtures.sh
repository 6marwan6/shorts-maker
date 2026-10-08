#!/usr/bin/env bash
# Regenerates packages/fixtures/media/*.mp4 from scratch. Offline: uses ffmpeg's built-in
# `flite` filter (libflite) for speech synthesis and `lavfi` color/noise sources for
# everything else -- no network access, no external TTS/API dependency (impl plan 0.9).
#
# Not byte-reproducible run-to-run (encoder/container timestamps vary slightly across ffmpeg
# builds), but spec-reproducible: durations, word counts, exact transcript text, speaker
# turns and onset/settle timestamps are fixed by this script and recorded in the matching
# <name>.ground_truth.json files -- that is the durable contract, checked by
# tests/unit/test_phase0_fixtures.py, not a byte-for-byte diff.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="$HERE/../packages/fixtures/media"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

mkvid() { # duration label color outfile
  ffmpeg -y -f lavfi -i "color=c=${3}:s=640x360:r=24:d=${1}" \
    -vf "drawtext=text='${2}':fontcolor=white:fontsize=28:x=(w-text_w)/2:y=(h-text_h)/2:box=1:boxcolor=black@0.4:boxborderw=10" \
    -c:v libx264 -pix_fmt yuv420p "${4}" -loglevel error
}

mux() { # video audio outfile
  ffmpeg -y -i "$1" -i "$2" \
    -c:v libx264 -pix_fmt yuv420p -profile:v baseline -c:a aac -b:a 96k -shortest \
    -map_metadata -1 -movflags +faststart "$3" -loglevel error
}

echo "== fixture_speech_45s.mp4 (144 words, 1 speaker, ~46.7s) =="
cat > "$TMP/speech_long.txt" << 'EOF'
Here's the thing nobody tells you about building a video editing pipeline. You cannot just cut clips at random points and hope for the best. The first rule is that every cut has to land on a safe boundary, somewhere the audio is quiet enough that a listener never notices the seam. The second rule is that the story has to survive the cut. If you remove the setup but keep the punchline, nobody understands why it's funny. So the system has to understand structure before it understands editing. It has to find where an idea begins and where it truly ends. Only then can it start deciding what to keep and what to throw away. That's the whole philosophy behind this project, and it's why we spent so much time on the boundary detection before writing a single line of the editor itself.
EOF
ffmpeg -y -f lavfi -i "flite=textfile=$TMP/speech_long.txt:voice=kal" -ar 16000 -ac 1 "$TMP/speech_long.wav" -loglevel error
mkvid 47 "SPEAKER A" 0x2b2b52 "$TMP/speech_long_v.mp4"
mux "$TMP/speech_long_v.mp4" "$TMP/speech_long.wav" "$OUT/fixture_speech_45s.mp4"

echo "== fixture_speech_lt25words.mp4 (16 words, ~5.1s) =="
cat > "$TMP/speech_short.txt" << 'EOF'
Quick question. Have you ever wondered why some short clips do so much better than others?
EOF
ffmpeg -y -f lavfi -i "flite=textfile=$TMP/speech_short.txt:voice=slt" -ar 16000 -ac 1 "$TMP/speech_short.wav" -loglevel error
mkvid 8 "SPEAKER A" 0x225577 "$TMP/speech_short_v.mp4"
mux "$TMP/speech_short_v.mp4" "$TMP/speech_short.wav" "$OUT/fixture_speech_lt25words.mp4"

echo "== fixture_event_6_8s.mp4 (7.0s: quiet -> onset at t=2.0s -> settle at t=2.3s) =="
ffmpeg -y -f lavfi -i "anoisesrc=color=pink:sample_rate=16000:amplitude=0.01:duration=2.0" "$TMP/a1.wav" -loglevel error
ffmpeg -y -f lavfi -i "anoisesrc=color=white:sample_rate=16000:amplitude=0.9:duration=0.3" "$TMP/a2.wav" -loglevel error
ffmpeg -y -f lavfi -i "anoisesrc=color=pink:sample_rate=16000:amplitude=0.01:duration=4.7" "$TMP/a3.wav" -loglevel error
printf "file 'a1.wav'\nfile 'a2.wav'\nfile 'a3.wav'\n" > "$TMP/aconcat.txt"
ffmpeg -y -f concat -safe 0 -i "$TMP/aconcat.txt" -c copy "$TMP/event_audio.wav" -loglevel error
mkvid 2.0 "" 0x1a1a2e "$TMP/v1.mp4"
mkvid 0.3 "" white "$TMP/v2.mp4"
mkvid 4.7 "" 0x1a1a2e "$TMP/v3.mp4"
printf "file 'v1.mp4'\nfile 'v2.mp4'\nfile 'v3.mp4'\n" > "$TMP/vconcat.txt"
ffmpeg -y -f concat -safe 0 -i "$TMP/vconcat.txt" -c copy "$TMP/event_video.mp4" -loglevel error
mux "$TMP/event_video.mp4" "$TMP/event_audio.wav" "$OUT/fixture_event_6_8s.mp4"

echo "== fixture_multi_speaker.mp4 (2 speakers, 4 turns, ~19.4s) =="
cat > "$TMP/sp_a1.txt" << 'EOF'
So here's what I don't get about this whole approach.
EOF
cat > "$TMP/sp_b1.txt" << 'EOF'
Okay, what's the problem with it?
EOF
cat > "$TMP/sp_a2.txt" << 'EOF'
Why does the system need to understand structure before it can even start editing anything?
EOF
cat > "$TMP/sp_b2.txt" << 'EOF'
Because a cut that ignores structure destroys the story, even if the audio sounds clean.
EOF
ffmpeg -y -f lavfi -i "flite=textfile=$TMP/sp_a1.txt:voice=rms" -ar 16000 -ac 1 "$TMP/msa1.wav" -loglevel error
ffmpeg -y -f lavfi -i "flite=textfile=$TMP/sp_b1.txt:voice=slt" -ar 16000 -ac 1 "$TMP/msb1.wav" -loglevel error
ffmpeg -y -f lavfi -i "flite=textfile=$TMP/sp_a2.txt:voice=rms" -ar 16000 -ac 1 "$TMP/msa2.wav" -loglevel error
ffmpeg -y -f lavfi -i "flite=textfile=$TMP/sp_b2.txt:voice=slt" -ar 16000 -ac 1 "$TMP/msb2.wav" -loglevel error
ffmpeg -y -f lavfi -i "anullsrc=r=16000:cl=mono" -t 0.6 "$TMP/sil.wav" -loglevel error
printf "file 'msa1.wav'\nfile 'sil.wav'\nfile 'msb1.wav'\nfile 'sil.wav'\nfile 'msa2.wav'\nfile 'sil.wav'\nfile 'msb2.wav'\n" > "$TMP/msconcat.txt"
ffmpeg -y -f concat -safe 0 -i "$TMP/msconcat.txt" -c copy "$TMP/ms_audio.wav" -loglevel error
# durations measured from the above (see ground_truth.json for exact turn boundaries)
mkvid 3.77 "SPEAKER A" 0x2b2b52 "$TMP/msv_a1.mp4"
mkvid 0.6  "SPEAKER A" 0x2b2b52 "$TMP/msv_sil1.mp4"
mkvid 2.23 "SPEAKER B" 0x552b2b "$TMP/msv_b1.mp4"
mkvid 0.6  "SPEAKER B" 0x552b2b "$TMP/msv_sil2.mp4"
mkvid 5.895 "SPEAKER A" 0x2b2b52 "$TMP/msv_a2.mp4"
mkvid 0.6  "SPEAKER A" 0x2b2b52 "$TMP/msv_sil3.mp4"
mkvid 5.70 "SPEAKER B" 0x552b2b "$TMP/msv_b2.mp4"
printf "file 'msv_a1.mp4'\nfile 'msv_sil1.mp4'\nfile 'msv_b1.mp4'\nfile 'msv_sil2.mp4'\nfile 'msv_a2.mp4'\nfile 'msv_sil3.mp4'\nfile 'msv_b2.mp4'\n" > "$TMP/msvconcat.txt"
ffmpeg -y -f concat -safe 0 -i "$TMP/msvconcat.txt" -c copy "$TMP/ms_video.mp4" -loglevel error
mux "$TMP/ms_video.mp4" "$TMP/ms_audio.wav" "$OUT/fixture_multi_speaker.mp4"

echo "== fixture_screen_content.mp4 (34 words, ~11.3s, screen-sized white quad) =="
cat > "$TMP/screen_narration.txt" << 'EOF'
As you can see on the screen right here, the boundary map lists every candidate cut point along with its confidence score, so you can trace exactly why the system chose this particular edit.
EOF
ffmpeg -y -f lavfi -i "flite=textfile=$TMP/screen_narration.txt:voice=awb" -ar 16000 -ac 1 "$TMP/screen_audio.wav" -loglevel error
ffmpeg -y -f lavfi -i "color=c=0x111111:s=640x360:r=24:d=12" \
  -vf "drawbox=x=80:y=40:w=480:h=270:color=white@0.92:t=fill,drawbox=x=80:y=40:w=480:h=270:color=black@0.9:t=6,drawtext=text='SCREEN CONTENT':fontcolor=black:fontsize=22:x=(w-text_w)/2:y=(h-text_h)/2" \
  -c:v libx264 -pix_fmt yuv420p "$TMP/screen_video.mp4" -loglevel error
mux "$TMP/screen_video.mp4" "$TMP/screen_audio.wav" "$OUT/fixture_screen_content.mp4"

echo "Done. Regenerate ground-truth JSON manually if any text/timing above was changed --"
echo "packages/fixtures/media/*.ground_truth.json is the checked contract, not this script's output."

# --- Phase 3 real-model smoke (owner 2026-10-06): non-English fixture. Needs `espeak-ng` (offline).
# Not run by default above because flite has no non-English voices; regenerate manually:
#   espeak-ng -v fr -s 150 -f fr.txt -w fr_raw.wav && ffmpeg -i fr_raw.wav -ar 16000 -ac 1 fr.wav
#   then mkvid + mux exactly like the English speech fixtures -> fixture_speech_non_english_fr.mp4
# Ground truth: packages/fixtures/media/fixture_speech_non_english_fr.ground_truth.json
