from collections import defaultdict
from os import path
from typing import List, Dict, Optional
from multiprocessing import Pool
from utils.llm_client import LlmClient, SpeechCategory, GeminiMultiClient
from utils.json_utils import (
    read_checkpoint_index,
    write_checkpoint_index,
    read_jsonl,
    append_to_jsonl
)
import time
import logging
from retry import retry


class EntityType:
    COMMENT: str = "comment"
    REPLY: str = "reply"


class RedditAnalyzer:
    def __init__(
        self,
        comments: List[Dict],
        replies: List[Dict],
        output_path: str,
        checkpoint_path: str,
        batch_size: int = 1000
    ):
        self.comments = []
        for comment in comments:
            comment["type"] = EntityType.COMMENT
            comment["parent_id"] = comment["post_id"]
            self.comments.append(comment)

        self.replies = defaultdict(list)
        for reply in replies:
            reply["type"] = EntityType.REPLY
            reply["parent_id"] = reply["parent_comment_id"]
            self.replies[reply["parent_id"]].append(reply)

        self.output_path = output_path
        self.checkpoint_path = checkpoint_path
        self.visited_replies = set()
        self.visited_comments = set()
        self.batch_size = batch_size

    @retry(
        exceptions=Exception,
        tries=5,
        delay=2,
        backoff=2,
        max_delay=60,
    )
    def analyze_replies(self, parent_id, llm_client: LlmClient):
        hate_speech_count = 0
        counter_hate_speech_count = 0
        total_replies = 0
        for entry in self.replies[parent_id]:
            if entry["id"] in self.visited_replies:
                continue
            # print(f"processing reply: {entry['id']}")
            self.visited_replies.add(entry["id"])
            total_replies += 1
            reply_category = llm_client.get_counter_speech_category(
                entry['body'])

            if reply_category == SpeechCategory.HATE_SPEECH:
                hate_speech_count += 1
            elif reply_category == SpeechCategory.COUNTER_HATE_SPEECH:
                counter_hate_speech_count += 1

            sub_reply_stats = self.analyze_replies(entry['id'], llm_client)
            hate_speech_count += sub_reply_stats['hate_speech_count']
            counter_hate_speech_count += sub_reply_stats['counter_hate_speech_count']
            total_replies += sub_reply_stats['total_replies']

        return {
            'hate_speech_count': hate_speech_count,
            'counter_hate_speech_count': counter_hate_speech_count,
            'total_replies': total_replies
        }

    def process(self):
        results = []
        start = read_checkpoint_index(self.checkpoint_path)
        print("Process entries:", len(self.comments))
        print("Starting at index:", start)

        for i in range(start+1, len(self.comments), self.batch_size):
            batch = self.comments[i:i + self.batch_size]
            batch_results = self.process_batch(batch)

            results.extend(batch_results)
            append_to_jsonl(batch_results, self.output_path)
            last_processed_index = i + len(batch) - 1
            write_checkpoint_index(self.checkpoint_path, last_processed_index)

            print(
                f"Processed {last_processed_index + 1} records with {len(results)} hate comments. Stopped at index {last_processed_index}"
            )

    def process_batch(self, batch):
        start_time = time.time()
        with Pool() as pool:
            batch_results = pool.map(self.process_entry, batch)
        end_time = time.time()  # Record the end time
        print(
            f"It took {end_time - start_time} seconds to process {len(batch)} entries")
        return [result for result in batch_results if result]

    @retry(
        exceptions=Exception,
        tries=5,
        delay=2,
        backoff=2,
        max_delay=60,
    )
    def process_entry(self, entry: Dict) -> Optional[Dict]:
        logging.info(f"Processing entry {entry}")
        speech = entry["body"].strip()
        gemini_client = GeminiMultiClient(parent_speech=speech)
        if (
            speech != "[removed]" and
            speech != "[deleted]" and
            gemini_client.is_hate_speech(speech)
            and entry["id"] not in self.visited_comments
        ):
            # print("Processing hate speech:", entry["body"])
            self.visited_comments.add(entry['id'])
            reply_stats = self.analyze_replies(
                entry['id'],
                gemini_client,
            )
            return {
                'type': entry['type'],
                'parent_speech': entry['body'],
                'hate_speech_counts': reply_stats['hate_speech_count'],
                'counter_hate_speech_count': reply_stats['counter_hate_speech_count'],
                'total_replies': reply_stats['total_replies'],
                'score': entry['score'],
                'id': entry['id'],
                'original_total_replies': entry['total_replies'],
            }
        logging.info(f"Done Processing entry {entry}")
        return None


if __name__ == "__main__":
    output_directory = './reddit/data/'
    comments = read_jsonl(path.join(output_directory, 'comments.jsonl'))
    replies = read_jsonl(path.join(output_directory, 'replies.jsonl'))
    output_path = "output.jsonl"
    checkpoint_path = "checkpoint.txt"
    analyzer = RedditAnalyzer(
        comments=comments,
        replies=replies,
        output_path=path.join(output_directory, 'hate_output.jsonl'),
        checkpoint_path=path.join(
            output_directory, 'hate_output_checkpoint.txt'),
        batch_size=800
    )
    analyzer.process()
