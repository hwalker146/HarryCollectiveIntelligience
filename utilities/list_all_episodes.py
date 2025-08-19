#!/usr/bin/env python3
"""
List all episodes from master transcript files
"""
import os
import re
from pathlib import Path

def list_episodes_in_file(file_path):
    """Extract all episodes from a master transcript file."""
    print(f"\n{'='*80}")
    print(f"FILE: {os.path.basename(file_path)}")
    print(f"{'='*80}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        episodes = []
        
        # Find all episode sections
        # Split by date headers first
        date_sections = re.split(r'\n## (\d{4}-\d{2}-\d{2})\n', content)
        
        if len(date_sections) < 2:
            print("No date sections found")
            return episodes
            
        # Process each date section
        for i in range(1, len(date_sections), 2):
            if i + 1 < len(date_sections):
                date_str = date_sections[i]
                section_content = date_sections[i + 1]
                
                # Find episodes in this date section
                episode_parts = re.split(r'\n### ([^\n]+)\n', section_content)
                
                for j in range(1, len(episode_parts), 2):
                    if j + 1 < len(episode_parts):
                        title = episode_parts[j]
                        episode_content = episode_parts[j + 1]
                        
                        # Extract episode ID
                        episode_id_match = re.search(r'\*\*Episode ID:\*\* (\d+)', episode_content)
                        episode_id = episode_id_match.group(1) if episode_id_match else "UNKNOWN"
                        
                        # Extract publication date  
                        pub_date_match = re.search(r'\*\*Publication Date:\*\* ([^\n]+)', episode_content)
                        pub_date = pub_date_match.group(1) if pub_date_match else "UNKNOWN"
                        
                        episodes.append({
                            'date': date_str,
                            'title': title,
                            'episode_id': episode_id,
                            'pub_date': pub_date
                        })
                        
                        print(f"{len(episodes):3d}. {date_str} - \"{title}\" (Episode ID: {episode_id})")
        
        print(f"\nTOTAL EPISODES FOUND: {len(episodes)}")
        return episodes
        
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        return []

def main():
    """List all episodes from all master transcript files."""
    transcripts_dir = "/Users/hwalker/Desktop/podcast_processor/podcast_app_v2/content/master_transcripts"
    
    total_episodes = 0
    
    # Process ALL transcript files
    for filename in sorted(os.listdir(transcripts_dir)):
        if filename.endswith('.md') and 'Transcript' in filename:
            file_path = os.path.join(transcripts_dir, filename)
            episodes = list_episodes_in_file(file_path)
            total_episodes += len(episodes)
    
    print(f"\n{'='*80}")
    print(f"GRAND TOTAL EPISODES ACROSS ALL FILES: {total_episodes}")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()