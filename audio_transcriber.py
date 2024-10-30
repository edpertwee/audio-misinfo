# %%
import os
import shutil
from pydub import AudioSegment
import openai
from pydub.silence import split_on_silence
from filecmp import cmp
from pathlib import Path
import sox

# %%
# Load OpenAI API key from a file
with open('openai_api_key.txt', 'r') as key_file:
    openai.api_key = key_file.readline().strip()

# Create an API client
client = openai.OpenAI(api_key = openai.api_key)

# %%
# Define constants
MAX_FILE_SIZE_MB = 25
AUDIO_CHUNK_LENGTH_MS = 10 * 60 * 1000  # 10 minutes in milliseconds
SOURCE_DIR = './audio'
TEMP_DIR = './temp'
TRANSCRIPT_DIR = './transcripts/unprocessed'

# %%
def check_create_new_dir(directory):
    """Creates a directory if it does not already exist.
    
    Args:
        directory: Path to the new directory.
    """

    if not os.path.exists(directory):
        os.mkdir(directory)

# %%
def copy_to_temp_dir(src, dest):
    """Copies audio files (mp3 and m4a) to temporary directory.
    
    Args:
        src (str): Path to source directory containing audio files.
        dest (str): Path to (temporary) destination directory.
    """
    for path, subdirs, files in os.walk(src):
        for name in files:
            (shortname, extension) = os.path.splitext(name)
            if extension == ".mp3":
                filename = os.path.join(path, name)
                shutil.copy2(filename, dest)
            elif extension == ".m4a":
                filename = os.path.join(path, name)
                shutil.copy2(filename, dest)

# %%
def convert_to_mp3(directory):

    """Converts m4a files to mp3
    
    Args:
        directory (str): Path to directory with audio files
        
    Returns:
        Converted audio as .mp3 in same directory"""
    
    for filename in os.listdir(directory):
        if filename.endswith('.m4a'):
            file_path = os.path.join(directory, filename)
            audio = AudioSegment.from_file(file_path, format="m4a")
            audio.export(os.path.splitext(file_path)[0] + ".mp3", format="mp3")
            os.remove(file_path)

# %%
def find_delete_duplicates(directory):
    """Finds and removes duplicate audio files from temp directory.
    Saves list of duplicates as .txt file in source directory.
    """

    # list of all documents 
    directory = Path(directory)
    files = sorted(os.listdir(directory))
    total_files = len(files) 
  
    # List having the classes of documents 
    # with the same content 
    duplicate_files = [] 
  
    # comparison of the documents 
    for file_x in files: 
  
        if_dupl = False
  
        for class_ in duplicate_files: 
            # Comparing files having same content using cmp() 
            # class_[0] represents a class having same content 
            if_dupl = cmp( 
                directory / file_x, 
                directory / class_[0], 
                shallow=False
            ) 
            if if_dupl: 
                class_.append(file_x) 
                break
    
        if not if_dupl: 
            duplicate_files.append([file_x]) 
    
    # Save results to file 
    print(duplicate_files)
    output_file = open(SOURCE_DIR+"/"+'audio_duplicates.txt', 'w')

    for item in duplicate_files:
        output_file.write(str(item) + '\n')

    # remove the duplicates
    for class_ in duplicate_files:
        for file in class_[1:]:
            os.remove(directory / file)

    # Print number of deleted files
    remaining_files = len(sorted(os.listdir(directory)))
    deleted_files = total_files - remaining_files
    print("Deleted " + str(deleted_files) + " files, "
          + str(remaining_files) + " remaining.")


# %%
def calculate_duration(directory):
    duration = sum([sox.file_info.duration(f) for f in Path(directory).glob('*.mp3')])
    hours = int(duration) // 3600  # calculate in hours 
    duration %= 3600
    mins = int(duration) // 60  # calculate in minutes 
    duration %= 60
    seconds = int(duration)  # calculate in seconds 
  
    print("Total audio to transcribe: " + str(hours) + "H:"
          + str(mins) + "M:" + str(seconds) + "S")

# %%
def split_audio(file_path):
    sound = AudioSegment.from_file(file_path)
    chunks = split_on_silence(
        sound,
        min_silence_len = 500,
        silence_thresh = sound.dBFS - 16,
        keep_silence = 250, # optional
    )
    
    audio_chunks = [chunks[0]]

    for chunk in chunks[1:]:
        if len(audio_chunks[-1]) < AUDIO_CHUNK_LENGTH_MS:
            audio_chunks[-1] += chunk
        else:
            # if the last output chunk
            # is longer than the target length,
            # we can start a new one
            audio_chunks.append(chunk)

    return audio_chunks

# %%
def transcribe_chunk(chunk, prompt=""):
    """Transcribes an audio chunk using OpenAI's Whisper API.
    
    Args:
        chunk (AudioSegment): Audio segment to be transcribed.
        prompt (str, optional): Additional text to help guide the transcription. Defaults to "".
        
    Returns:
        str: Transcription of the audio chunk.
    """
    # Save chunk to a temporary file
    temp_file = "temp_chunk.mp3"
    chunk.export(temp_file, format="mp3")
    
    with open(temp_file, "rb") as audio_file:
        # Pass the prompt parameter to the transcription API
        transcript = client.audio.transcriptions.create(
            model = "whisper-1",
            file = audio_file,
            prompt=prompt)
    
    # Remove temporary file
    os.remove(temp_file)
    
    return transcript

# %%
def transcribe_all(directory):
    """Main function to transcribe audio files in a directory."""
    
    counter_1 = 1
    total_files = len([f for f in os.listdir("./temp")
                       if f.endswith('.mp3') and 
                       os.path.isfile(os.path.join("./temp", f))])

    for filename in os.listdir(directory):
        if filename.endswith('.mp3'):
            file_path = os.path.join(directory, filename)
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            print("Processing file " + str(counter_1) + " of " \
                   + str(total_files) + "...")
            print("File name: " + str(filename))
            print("File size: " + str(file_size_mb) + " mb")
            
            # If the file is larger than the MAX_FILE_SIZE_MB, split it into chunks
            if file_size_mb > MAX_FILE_SIZE_MB:
                print("Splitting file into chunks...")
                audio_chunks = split_audio(file_path)
                transcriptions = []
                previous_transcript = ""  # Initialize an empty previous transcript
                print("Initializing empty transcript...")
                
                counter_2 = 1

                for chunk in audio_chunks:
                    # Prepend the previous transcript to the chunk transcription
                    transcript_chunk = transcribe_chunk(chunk)
                    transcriptions.append(transcript_chunk.text)
                    # Update previous_transcript for the next chunk
                    previous_transcript = transcript_chunk
                    print("Transcribed chunk " + str(counter_2) \
                          + " of " + str(len(audio_chunks)))
                    counter_2 = counter_2 + 1
                
                print("Joining transcriptions")
                full_transcription = '\n'.join(transcriptions)
                
            else:
                # If the file is smaller than the maximum size, transcribe it directly
                print("Transcribing file directly")
                with open(file_path, "rb") as audio_file:
                    transcription = client.audio.transcriptions.create(
                        model = "whisper-1", file = audio_file)
                    full_transcription = transcription.text
            
            # Write transcription to a .txt file
            print("Writing transcription to file")
            with open(os.path.splitext(file_path)[0] + '.txt', 'w') as txt_file:
                txt_file.write(full_transcription)
        
            print("Purging temporary audio file")
            os.remove(file_path)

            counter_1 = counter_1 + 1

# %%
def move_to_perm_dir(src, dest):
    """Copies transcript files (txt) to permanent directory.
    
    Args:
        src (str): Path to source directory containing transcripts.
        dest (str): Path to (permanent) destination directory.
    """
    for path, subdirs, files in os.walk(src):
        for name in files:
            (shortname, extension) = os.path.splitext(name)
            if extension == ".txt":
                filename = os.path.join(path, name)
                shutil.move(filename, dest)
    
    try:
        os.rmdir(src)
        print("Successfully purged temporary directory.")
    except:
        print("Could not purge temporary directory. Still contains files.")

# %%
check_create_new_dir(TEMP_DIR)

# %%
copy_to_temp_dir(SOURCE_DIR, TEMP_DIR)

# %%
convert_to_mp3(TEMP_DIR)

# %%
find_delete_duplicates(TEMP_DIR)

# %%
calculate_duration(TEMP_DIR)

# %%
transcribe_all(TEMP_DIR)

# %%
check_create_new_dir(TRANSCRIPT_DIR)

# %%
move_to_perm_dir(TEMP_DIR, TRANSCRIPT_DIR)

# %%
count = len([f for f in os.listdir("./temp") 
     if f.endswith('.mp3') and os.path.isfile(os.path.join("./temp", f))])
print(count)


