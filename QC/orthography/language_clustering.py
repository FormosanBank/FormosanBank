from multiprocessing.util import debug
import os
import scipy
import sklearn
from orthography_extract import remove_chinese_characters
from collections import Counter
import xml.etree.ElementTree as ET
from sklearn.manifold import TSNE
from sklearn.decomposition import TruncatedSVD, PCA
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm
import warnings
from collections import Counter
from sklearn.cluster import DBSCAN, KMeans
from orthography_compare import is_dialect
import argparse

warnings.filterwarnings("ignore")

CORPORA_PATH = "Corpora/"
IN_SCOPE_LANGS = ["ami", "tay", "bnn", "pwn", "pyu", "dru", "trv"]
# IN_SCOPE_LANGS = ["ami", "pwn"]

ISO_TO_LANGUAGE: dict[str, str] = {
    "ami": "Amis",
    "tay": "Atayal",
    "pwn": "Paiwan",
    "bnn": "Bunun",
    "pyu": "Puyuma",
    "dru": "Rukai",
    "tsu": "Tsou",
    "xsy": "Saisiyat",
    "tao": "Yami",
    "ssf": "Thao",
    "ckv": "Kavalan",
    "trv": "Seediq",
    "szy": "Sakizaya",
    "sxr": "Saaroa",
    "xnb": "Kanakanavu",
    "fos": "Siraya",
}
IN_SCOPE_NAMES = {ISO_TO_LANGUAGE[iso] for iso in IN_SCOPE_LANGS}


def load_file(tar_path):
    if tar_path.lower().endswith('.xml'):
        tree = ET.parse(tar_path)
        root = tree.getroot()
        text = []
        for sentence in root.findall('.//S'):
            form = sentence.find("FORM[@kindOf='standard']")
            if form is not None and form.text:
                text.append(form.text)
        return " ".join(text)

def get_language_from_file(tar_path):
    """Extract language (xml:lang) from the TEXT element"""
    if tar_path.lower().endswith('.xml'):
        tree = ET.parse(tar_path)
        root = tree.getroot()
        # Get xml:lang from the root TEXT element
        lang = root.get('{http://www.w3.org/XML/1998/namespace}lang')
        return lang if lang else 'Unknown'
    return 'Unknown'

def get_document_texts_by_lang(debug=False, limit=None):
    document_texts = {}
    document_languages = {}
    character_counts = {}
    total_found = 0
    for corpus in sorted(os.listdir(CORPORA_PATH)):
        corpus_path = os.path.join(CORPORA_PATH, corpus + "/XML/")
        if os.path.isdir(corpus_path):
            print(f"Processing corpus: {corpus}")
            # Recursively find all XML files
            for root, dirs, files in os.walk(corpus_path):
                for file in sorted(files):
                    if file.lower().endswith('.xml'):
                        if limit and total_found >= limit:
                            print(f"Reached limit of {limit} documents")
                            return document_texts, character_counts, document_languages
                        document_path = os.path.join(root, file)
                        try:
                            text = load_file(document_path)
                            if text:
                                language = get_language_from_file(document_path)
                                if language not in IN_SCOPE_LANGS:
                                    if debug:
                                        print(f"  Skipping {document_path} - Language: {language} not in scope")
                                    continue
                                text = remove_chinese_characters(text)
                                document_texts[document_path] = text
                                document_languages[document_path] = language
                                character_counts[document_path] = Counter(text)
                                total_found += 1
                                if debug or total_found % 10 == 0:
                                    print(f"  [{total_found}] {file} - Language: {language}")
                        except Exception as e:
                            print(f"  Error processing {document_path}: {e}")
    return document_texts, character_counts, document_languages

def get_dialect_from_file(tar_path):
    """Extract dialect (xml:lang) from the TEXT element"""
    if tar_path.lower().endswith('.xml'):
        tree = ET.parse(tar_path)
        root = tree.getroot()
        dialect = root.attrib.get('dialect', None)
        if dialect:
            return dialect
    return 'Unknown'

def get_document_texts_by_dialect(target_lang, debug=False, limit=None):
    document_texts = {}
    document_dialects = {}
    character_counts = {}
    total_found = 0
    for corpus in sorted(os.listdir(CORPORA_PATH)):
        print(f"Processing corpus: {corpus}")
        corpus_path = os.path.join(CORPORA_PATH, corpus + "/XML/")
        if os.path.isdir(corpus_path):
            # Recursively find all XML files
            for root, dirs, files in os.walk(corpus_path):
                for file in sorted(files):
                    if file.lower().endswith('.xml'):
                        if limit and total_found >= limit:
                            print(f"Reached limit of {limit} documents")
                            return document_texts, character_counts, document_dialects
                        document_path = os.path.join(root, file)
                        try:
                            text = load_file(document_path)
                            dialect = get_dialect_from_file(document_path)
                            if text and dialect and is_dialect(ISO_TO_LANGUAGE[target_lang], dialect):
                                language = get_language_from_file(document_path)
                                if language != target_lang:
                                    if debug:
                                        print(f"  Skipping {document_path} - Language: {language} not in scope")
                                    continue
                                text = remove_chinese_characters(text)
                                document_texts[document_path] = text
                                document_dialects[document_path] = dialect
                                character_counts[document_path] = Counter(text)
                                total_found += 1
                                if debug or total_found % 10 == 0:
                                    print(f"  [{total_found}] {file} - Dialect: {dialect}")
                        except Exception as e:
                            print(f"  Error processing {document_path}: {e}")
    return document_texts, character_counts, document_dialects


def texts_to_vectors(document_texts, vector_type: sklearn.feature_extraction.text=CountVectorizer):
    """Convert texts to feature vectors using CountVectorizer"""
    doc_paths = list(document_texts.keys())
    texts = list(document_texts.values())
    
    # Use CountVectorizer to convert texts to word counts
    vectorizer = vector_type()
    vectors = vectorizer.fit_transform(texts)
    
    print(f"{vector_type.__name__} vocabulary size: {len(vectorizer.get_feature_names_out())}")
    
    # Convert sparse matrix to dense array
    vectors_dense = vectors.toarray()
    
    return vectors_dense, doc_paths, vectorizer.get_feature_names_out()

def calculate_cluster_accuracy(reduced_points, languages, doc_paths):
    """
    Calculate clustering accuracy using KMeans clustering.
    Assigns documents to clusters and checks if each document's language
    matches the dominant language in its assigned cluster.
    
    Returns:
    - accuracy: float between 0 and 1
    - misclassified: list of indices that are misclassified
    """
    from sklearn.cluster import KMeans
    from collections import Counter
    
    # Determine number of clusters from unique languages
    unique_langs = set(languages.values())
    n_clusters = len(unique_langs)
    
    print(f"Running KMeans with {n_clusters} clusters...")
    
    # Perform KMeans clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=0, n_init=10)
    cluster_assignments = kmeans.fit_predict(reduced_points)
    
    # For each cluster, find the dominant language
    cluster_to_dominant_lang = {}
    for cluster_id in range(n_clusters):
        docs_in_cluster = [i for i, c in enumerate(cluster_assignments) if c == cluster_id]
        langs_in_cluster = [languages[doc_paths[i]] for i in docs_in_cluster]
        lang_counts = Counter(langs_in_cluster)
        cluster_to_dominant_lang[cluster_id] = lang_counts.most_common(1)[0][0]
    
    # Check accuracy: document language should match cluster's dominant language
    correctly_classified = 0
    misclassified = []
    
    for i in range(len(doc_paths)):
        assigned_cluster = cluster_assignments[i]
        cluster_dominant_lang = cluster_to_dominant_lang[assigned_cluster]
        doc_lang = languages[doc_paths[i]]
        
        if doc_lang == cluster_dominant_lang:
            correctly_classified += 1
        else:
            misclassified.append(i)
    
    accuracy = correctly_classified / len(doc_paths)
    return accuracy, misclassified

def calculate_dbscan_accuracy(cluster_labels, doc_paths, languages):
    """
    Calculate clustering accuracy for DBSCAN clusters.
    For each clustered point (cluster != -1), checks if its language matches 
    the dominant language in that cluster. Noise points (-1) are counted as misclassified.
    
    Returns:
    - accuracy: float between 0 and 1
    - misclassified: list of indices that are misclassified or noise
    - noise_points: list of noise point indices (cluster == -1)
    """
    from collections import Counter
    
    # Find dominant language for each cluster
    cluster_to_dominant_lang = {}
    unique_clusters = set(cluster_labels)
    
    for cluster_id in unique_clusters:
        if cluster_id == -1:  # Skip noise
            continue
        docs_in_cluster = [i for i, c in enumerate(cluster_labels) if c == cluster_id]
        langs_in_cluster = [languages[doc_paths[i]] for i in docs_in_cluster]
        lang_counts = Counter(langs_in_cluster)
        cluster_to_dominant_lang[cluster_id] = lang_counts.most_common(1)[0][0]
    
    # Check accuracy: document language should match cluster's dominant language
    correctly_classified = 0
    misclassified = []
    noise_points = []
    
    for i in range(len(doc_paths)):
        assigned_cluster = cluster_labels[i]
        
        if assigned_cluster == -1:
            # Noise points are counted as misclassified
            misclassified.append(i)
            noise_points.append(i)
        else:
            cluster_dominant_lang = cluster_to_dominant_lang[assigned_cluster]
            doc_lang = languages[doc_paths[i]]
            
            if doc_lang == cluster_dominant_lang:
                correctly_classified += 1
            else:
                misclassified.append(i)
    
    accuracy = correctly_classified / len(doc_paths)
    return accuracy, misclassified, noise_points

def apply_dimensionality_reduction(vectors, method='SVD', n_components=100):
    """Apply dimensionality reduction and return reduced vectors with explained variance"""
    print(f"\nApplying {method} to reduce to {n_components} dimensions...")
    
    if method == 'SVD':
        reducer = TruncatedSVD(n_components=n_components, random_state=0)
    elif method == 'PCA':
        reducer = PCA(n_components=n_components, random_state=0)
    else:
        raise ValueError(f"Unsupported dimensionality reduction method: {method}")
    
    vectors_reduced = reducer.fit_transform(vectors)
    explained_var = reducer.explained_variance_ratio_.sum()
    print(f"Explained variance ratio: {explained_var:.2%}")
    
    return vectors_reduced, explained_var

def visualize_tsne(doc_paths, languages, title, output_file, vectors_reduced, p=15, sim_metric='euclidean'):
    """Apply t-SNE to pre-reduced vectors and create visualization"""
    print(f"Applying t-SNE for {title}...")
    tsne = TSNE(n_components=2, random_state=0, n_iter=10000, perplexity=p, metric=sim_metric)
    reduced = tsne.fit_transform(vectors_reduced)
    
    # Calculate cluster accuracy using KMeans
    accuracy, misclassified = calculate_cluster_accuracy(reduced, languages, doc_paths)
    print(f"Cluster Accuracy: {accuracy:.2%} ({len(doc_paths) - len(misclassified)}/{len(doc_paths)} correctly clustered)")
    
    # Create unique colors for each language
    unique_langs = sorted(set(languages.values()))
    colors = cm.get_cmap('tab20', len(unique_langs))
    lang_to_color = {lang: colors(i) for i, lang in enumerate(unique_langs)}
    
    # Create visualization
    fig, ax = plt.subplots(figsize=(14, 10))
    
    misclassified_set = set(misclassified)
    
    for lang in unique_langs:
        # Correctly classified documents for this language
        correct_mask = [i for i, dp in enumerate(doc_paths) 
                       if languages[dp] == lang and i not in misclassified_set]
        # Incorrectly classified documents for this language
        incorrect_mask = [i for i, dp in enumerate(doc_paths) 
                         if languages[dp] == lang and i in misclassified_set]
        
        # Plot correctly classified with circles
        if correct_mask:
            x = reduced[correct_mask, 0]
            y = reduced[correct_mask, 1]
            ax.scatter(x, y, label=f'{lang} (correct)', alpha=0.6, s=50, 
                      marker='o', color=lang_to_color[lang])
        
        # Plot incorrectly classified with X marker
        if incorrect_mask:
            x = reduced[incorrect_mask, 0]
            y = reduced[incorrect_mask, 1]
            ax.scatter(x, y, label=f'{lang} (incorrect)', alpha=0.8, s=100, 
                      marker='x', linewidths=2, color=lang_to_color[lang])
    
    if tsne.n_components == 2:
        ax.set_xlabel('t-SNE Component 1')
        ax.set_ylabel('t-SNE Component 2')
    if tsne.n_components == 3:
        ax = fig.add_subplot(111, projection='3d')
        ax.set_xlabel('t-SNE Component 1')
        ax.set_ylabel('t-SNE Component 2')
        ax.set_zlabel('t-SNE Component 3')
    ax.set_title(title)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=7)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"Visualization saved to {output_file}")
    plt.close()

def visualize_dbscan(doc_paths, languages, title, output_file, vectors_reduced, vectors_2d, eps=0.5, min_samples=5, sim_metric='euclidean'):
    """Apply DBSCAN to pre-reduced vectors and create visualization"""
    print(f"Applying DBSCAN for {title}...")
    dbscan = DBSCAN(eps=eps, min_samples=min_samples, metric=sim_metric)
    cluster_labels = dbscan.fit_predict(vectors_reduced)
    
    # Calculate accuracy
    accuracy, misclassified, noise_points = calculate_dbscan_accuracy(cluster_labels, doc_paths, languages)
    n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
    n_noise = sum(1 for c in cluster_labels if c == -1)
    print(f"DBSCAN found {n_clusters} clusters with {n_noise} noise points")
    print(f"Cluster Accuracy: {accuracy:.2%} ({len(doc_paths) - len(misclassified)}/{len(doc_paths)} correctly clustered)")
    if n_noise > 0:
        print(f"  - {n_noise} noise points (treated as misclassified)")
    
    # Create unique colors for each cluster
    unique_clusters = sorted(set(cluster_labels))
    colors = cm.get_cmap('tab20', len(unique_clusters))
    cluster_to_color = {cluster: colors(i) for i, cluster in enumerate(unique_clusters)}
    
    # Create visualization with all points
    fig, ax = plt.subplots(figsize=(14, 10))
    
    misclassified_set = set(misclassified)
    
    for cluster in unique_clusters:
        if cluster == -1:
            # Plot noise points separately with small X markers
            mask = [i for i, c in enumerate(cluster_labels) if c == cluster]
            x = vectors_2d[mask, 0]
            y = vectors_2d[mask, 1]
            ax.scatter(x, y, label='Noise', alpha=0.3, s=30, marker='x', 
                      linewidths=1, color='gray')
        else:
            mask = [i for i, c in enumerate(cluster_labels) if c == cluster]
            # Separate correctly and incorrectly classified
            correct_mask = [i for i in mask if i not in misclassified_set]
            incorrect_mask = [i for i in mask if i in misclassified_set]
            
            if correct_mask:
                x = vectors_2d[correct_mask, 0]
                y = vectors_2d[correct_mask, 1]
                ax.scatter(x, y, label=f'Cluster {cluster} (correct)', alpha=0.6, s=50, 
                          marker='o', color=cluster_to_color[cluster])
            
            if incorrect_mask:
                x = vectors_2d[incorrect_mask, 0]
                y = vectors_2d[incorrect_mask, 1]
                ax.scatter(x, y, label=f'Cluster {cluster} (incorrect)', alpha=0.8, s=100, 
                          marker='X', linewidths=1.5, color=cluster_to_color[cluster])
    
    ax.set_xlabel('SVD Component 1')
    ax.set_ylabel('SVD Component 2')
    ax.set_title(f'{title}\nAccuracy: {accuracy:.2%}')
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=7)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"DBSCAN visualization saved to {output_file}")
    plt.close()
    
    # Create a second visualization excluding noise points for better clarity
    if n_noise > 0:
        fig, ax = plt.subplots(figsize=(14, 10))
        
        for cluster in unique_clusters:
            if cluster == -1:
                continue
            
            mask = [i for i, c in enumerate(cluster_labels) if c == cluster]
            correct_mask = [i for i in mask if i not in misclassified_set]
            incorrect_mask = [i for i in mask if i in misclassified_set]
            
            if correct_mask:
                x = vectors_2d[correct_mask, 0]
                y = vectors_2d[correct_mask, 1]
                ax.scatter(x, y, label=f'Cluster {cluster} (correct)', alpha=0.6, s=50, 
                          marker='o', color=cluster_to_color[cluster])
            
            if incorrect_mask:
                x = vectors_2d[incorrect_mask, 0]
                y = vectors_2d[incorrect_mask, 1]
                ax.scatter(x, y, label=f'Cluster {cluster} (incorrect)', alpha=0.8, s=100, 
                          marker='X', linewidths=1.5, color=cluster_to_color[cluster])
        
        ax.set_xlabel('SVD Component 1')
        ax.set_ylabel('SVD Component 2')
        ax.set_title(f'{title} (Clustered Points Only)\nAccuracy: {accuracy:.2%}')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=7)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        output_file_clustered = output_file.replace('.png', '_clustered_only.png')
        plt.savefig(output_file_clustered, dpi=150, bbox_inches='tight')
        print(f"DBSCAN clustered-only visualization saved to {output_file_clustered}")
        plt.close()

def visualize_kmeans(doc_paths, languages, title, output_file, vectors_reduced, vectors_2d):
    """Apply KMeans to pre-reduced vectors and create visualization"""
    kmeans = KMeans(n_clusters=len(set(languages.values())), random_state=0, init='k-means++')
    kmeans.fit(vectors_reduced)

    # Calculate cluster accuracy using KMeans
    accuracy, misclassified = calculate_cluster_accuracy(vectors_reduced, languages, doc_paths)
    print(f"Cluster Accuracy: {accuracy:.2%} ({len(doc_paths) - len(misclassified)}/{len(doc_paths)} correctly clustered)")

    # Create unique colors for each language
    unique_langs = sorted(set(languages.values()))
    colors = cm.get_cmap('tab20', len(unique_langs))
    lang_to_color = {lang: colors(i) for i, lang in enumerate(unique_langs)}
    
    plt.figure(figsize=(10, 8))
    for lang in unique_langs:
        mask = [i for i, dp in enumerate(doc_paths) if languages[dp] == lang]
        x = vectors_2d[mask, 0]
        y = vectors_2d[mask, 1]
        plt.scatter(x, y, label=lang, alpha=0.6, color=lang_to_color[lang])
    plt.xlabel('Component 1')
    plt.ylabel('Component 2')
    plt.title(f'{title} (KMeans Clustering)')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=7)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"KMeans visualization saved to {output_file}")
    plt.close()


def main():
    print("Loading documents...\n")
    # Load up to 1000 documents for visualization
    l = None
    if args.mode == 'lang':
        document_texts, char_counts, langs = get_document_texts_by_lang(debug=False, limit=l)
    elif args.mode == 'dialect':
        document_texts, char_counts, langs = get_document_texts_by_dialect(args.lang, debug=False, limit=l)
    
    if not document_texts:
        print("No documents found!")
        return
    
    print(f"\nLoaded {len(document_texts)} documents")
    
    # Print language distribution
    lang_counts = Counter(langs.values())
    print("\nLanguage distribution:")
    for lang, count in lang_counts.most_common():
        print(f"  {lang}: {count} documents")
    
    # Convert to vectors using TfidfVectorizer
    print("\nConverting texts to vectors using TfidfVectorizer...")
    word_vectors, doc_paths, vocab = texts_to_vectors(document_texts, TfidfVectorizer)
    print(f"Feature space dimension: {word_vectors.shape[1]}")
    
    # Create language mapping for doc_paths
    languages = {doc_paths[i]: langs[doc_paths[i]] for i in range(len(doc_paths))}
    
    n_d = 25

    if args.dr == 'SVD':
        reducer = TruncatedSVD(n_components=n_d, random_state=0)
        vectors_reduced = reducer.fit_transform(word_vectors)
        print(f"Explained variance ratio: {reducer.explained_variance_ratio_.sum():.2%}")
        
        # Further reduce to 2D for visualization
        print(f"Applying TruncatedSVD to 2D for visualization...")
        svd_2d = TruncatedSVD(n_components=2, random_state=0)
        vectors_2d = svd_2d.fit_transform(vectors_reduced)
    elif args.dr == 'PCA':
        reducer = PCA(n_components=n_d, random_state=0)
        vectors_reduced = reducer.fit_transform(word_vectors)
        print(f"Explained variance ratio: {reducer.explained_variance_ratio_.sum():.2%}")
        
        # Further reduce to 2D for visualization
        print(f"Applying PCA to 2D for visualization...")
        pca_2d = PCA(n_components=2, random_state=0)
        vectors_2d = pca_2d.fit_transform(vectors_reduced)
    
    # Visualize with t-SNE
    lang = args.lang if args.mode == 'dialect' else 'all'
    visualize_tsne(doc_paths, languages, 
                   f'Document Clustering by Language (Word-based Features) for {lang}', 
                   f'{args.mode}_word_tsne_clustering.png',
                   vectors_reduced,
                   p=35,
                   sim_metric='euclidean')

    # Visualize with DBSCAN
    visualize_dbscan(doc_paths, languages,
                     f'DBSCAN Clustering of Documents by Language (Word-based Features) for {lang}',
                     f'{args.mode}_word_dbscan_clustering.png',
                     vectors_reduced,
                     vectors_2d,
                     eps=0.5,
                     min_samples=5,
                     sim_metric='euclidean')
    
    # Visualize with KMeans
    visualize_kmeans(doc_paths, languages,
                     f'KMeans Clustering of Documents by Language (Word-based Features) for {lang}',
                     f'{args.mode}_word_kmeans_clustering.png',
                     vectors_reduced,
                     vectors_2d)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Document Clustering by Language")
    parser.add_argument('--mode', choices=['lang', 'dialect'], default='lang', help='Clustering mode to visualize')
    parser.add_argument('--lang', help='Language code to filter documents (e.g., ami, tay, pwn) for dialect mode', required=False)
    parser.add_argument('--dr' , choices=['SVD', 'PCA'], default='SVD', help='Dimensionality reduction method to use')

    args = parser.parse_args()
    if args.mode == 'dialect' and not args.lang:
        parser.error("Dialect mode requires a language code to be specified with --lang")
    elif args.mode == 'dialect' and args.lang not in IN_SCOPE_LANGS:
        parser.error(f"Language code '{args.lang}' is not in the list of supported languages: {IN_SCOPE_LANGS}")
    main()