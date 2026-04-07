import pandas as pd
import numpy as np, json
import json
import sys
from pathlib import Path
from sqlalchemy.orm import Session
from db import SessionLocal
from models import *
from pathlib import Path

parquet_path = r"D:\music_data\processed\ab_fma_v3.parquet"
embed_dir = r"D:\music_data\embeddings"


#load parquet
print("loading parquet...")
df = pd.read_parquet(parquet_path)
print(f"{len(df)} tracks found\n"
      f"{106407 - len(df)} tracks missing")

#connect to db
db:Session = SessionLocal()

inserted = 0
skipped = 0
no_embed = 0

print("Inserting tracks...\n\n")

for i, row in df.iterrows():
    fma_id = int(row['track_id'])

    existing = db.query(Track).filter_by(fma_track_id=fma_id).first()
    if existing:
        skipped += 1
        continue


    #tracks
    track = Track(
        fma_track_id=fma_id,
        title=str(row["title"]) if pd.notna(row["title"]) else "Unknown",
        artist=str(row["artist"]) if pd.notna(row["artist"]) else "Unknown",
        genre=str(row["genre"]) if pd.notna(row.get("genre")) else None,
        tempo=float(row["bpm"]) if pd.notna(row["bpm"]) else None,
        energy=float(row["energy"]) if pd.notna(row["energy"]) else None,
        key=str(int(row["key"])) if pd.notna(row["key"]) else None,
    )
    db.add(track)
    db.flush() # get track.id without committing

    #audio features
    af = AudioFeature(
        track_id = track.id,
        tempo = float(row["bpm"]) if pd.notna(row["bpm"]) else None,
        key = str(int(row["key"])) if pd.notna(row["key"]) else None,
        energy = float(row["energy"]) if pd.notna(row["energy"]) else None,

        danceability=None,
        valence=None,
        acousticness=None,
        instrumentalness=None,
        speechiness=None,
        liveness=None,


    )
    db.add(af)

    #song embeddings
    embed_path = Path(rf"D:\music_data\embeddings\{fma_id:06d}.npy")
    if embed_path.exists():
        vec = np.load(str(embed_path)).tolist()
        se = SongEmbedding(
            track_id = track.id,
            model_name = 'Clap',
            model_version ="v3",
            vector = vec,
        )
        db.add(se)
    else:
        no_embed += 1

    inserted += 1

    #commit every 500 rows to avoid large transactions
    if inserted % 500 ==0:
        db.commit()
        print(f"committed {inserted} tracks so far...")



#final commit
db.commit()
db.close()

print("\n Done!")
print(f"inserted {inserted} tracks")
print(f"skipped {skipped} tracks")
print(f"no_embed {no_embed} tracks")






