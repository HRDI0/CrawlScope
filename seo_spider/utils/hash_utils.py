"""
Hashing utilities for duplicate content detection.
Mirrors Screaming Frog's MD5-based duplicate detection.
"""
import hashlib
import re
from collections import Counter


def content_hash(content: str) -> str:
    """MD5 hash of content for exact duplicate detection."""
    return hashlib.md5(content.encode('utf-8', errors='ignore')).hexdigest()


def normalize_text(text: str) -> str:
    """Normalize text for comparison: lowercase, strip whitespace."""
    text = re.sub(r'\s+', ' ', text).strip().lower()
    return text


def simhash_text(text: str, hash_bits: int = 64) -> int:
    """
    SimHash for near-duplicate detection.
    Returns an integer fingerprint.
    """
    tokens = text.lower().split()
    if not tokens:
        return 0

    v = [0] * hash_bits
    for token in tokens:
        token_hash = int(hashlib.md5(token.encode()).hexdigest(), 16)
        for i in range(hash_bits):
            bitmask = 1 << i
            if token_hash & bitmask:
                v[i] += 1
            else:
                v[i] -= 1

    fingerprint = 0
    for i in range(hash_bits):
        if v[i] >= 0:
            fingerprint |= (1 << i)
    return fingerprint


def hamming_distance(hash1: int, hash2: int) -> int:
    """Calculate Hamming distance between two hashes."""
    x = hash1 ^ hash2
    count = 0
    while x:
        count += 1
        x &= x - 1
    return count


def are_near_duplicates(hash1: int, hash2: int, threshold: int = 3) -> bool:
    """Check if two SimHashes indicate near-duplicate content."""
    return hamming_distance(hash1, hash2) <= threshold


def shingle_hash(text: str, shingle_size: int = 4) -> set:
    """Create a set of shingle hashes for Jaccard similarity."""
    words = text.lower().split()
    if len(words) < shingle_size:
        return {content_hash(' '.join(words))}
    shingles = set()
    for i in range(len(words) - shingle_size + 1):
        shingle = ' '.join(words[i:i + shingle_size])
        shingles.add(content_hash(shingle))
    return shingles


def jaccard_similarity(set1: set, set2: set) -> float:
    """Calculate Jaccard similarity between two shingle sets."""
    if not set1 or not set2:
        return 0.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0
