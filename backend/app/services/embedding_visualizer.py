"""TensorFlow Embedding Projector 연동 - 썸네일 임베딩 시각화"""
from typing import List, Dict
import numpy as np
from pathlib import Path
import json
import logfire


class EmbeddingVisualizer:
    """
import logging
    Pinecone 임베딩을 TensorFlow Embedding Projector로 시각화

    사용 목적:
    - 고성과 vs 저성과 썸네일 패턴 시각적 비교
    - 자신의 컨텐츠 vs 타인의 컨텐츠 클러스터링
    - 플랫폼별 (YouTube, Facebook, Instagram) 임베딩 분포
    - t-SNE, PCA, UMAP으로 차원 축소 시각화
    """

    def __init__(self, output_dir: str = "./embeddings_viz"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)

    def export_for_projector(
        self,
        pinecone_index,
        user_id: str,
        max_vectors: int = 1000
    ) -> str:
        """
        Pinecone에서 임베딩 추출 후 TensorBoard Projector 형식으로 저장

        생성 파일:
        - embeddings.tsv: 벡터 데이터 (N x D)
        - metadata.tsv: 메타데이터 (제목, 성과, 플랫폼 등)

        Args:
            pinecone_index: Pinecone 인덱스
            user_id: 사용자 ID
            max_vectors: 최대 벡터 수

        Returns:
            출력 디렉토리 경로
        """
        with self.logger.span("embedding_viz.export"):
            # 1. Pinecone에서 벡터 조회
            # 모든 벡터 가져오기 (쿼리 벡터 없이)
            # Pinecone v3에서는 list() 사용
            try:
                # 더미 쿼리로 유사 벡터 가져오기
                dummy_vector = [0.0] * 512  # CLIP 벡터 차원

                # 자신의 컨텐츠
                own_results = pinecone_index.query(
                    vector=dummy_vector,
                    top_k=max_vectors // 2,
                    filter={"is_own_content": {"$eq": True}, "user_id": {"$eq": user_id}},
                    include_metadata=True,
                    include_values=True
                )

                # 타인의 컨텐츠
                others_results = pinecone_index.query(
                    vector=dummy_vector,
                    top_k=max_vectors // 2,
                    filter={"is_own_content": {"$ne": True}},
                    include_metadata=True,
                    include_values=True
                )

                all_vectors = own_results.get('matches', []) + others_results.get('matches', [])

            except Exception as e:
                self.logger.error(f"Pinecone query failed: {e}")
                # 폴백: 더미 데이터
                all_vectors = []

            if not all_vectors:
                self.logger.warning("No vectors found, using dummy data")
                return self._create_dummy_visualization()

            # 2. TSV 파일 생성
            embeddings_path = self.output_dir / "embeddings.tsv"
            metadata_path = self.output_dir / "metadata.tsv"

            with open(embeddings_path, 'w') as emb_file, \
                 open(metadata_path, 'w') as meta_file:

                # 메타데이터 헤더
                meta_file.write("Title\tPlatform\tPerformance\tViews\tOwnership\n")

                for match in all_vectors:
                    vector = match.get('values', [])
                    metadata = match.get('metadata', {})

                    # 벡터 저장 (탭 구분)
                    emb_file.write('\t'.join(map(str, vector)) + '\n')

                    # 메타데이터 저장
                    title = metadata.get('title', 'Unknown')[:50]  # 제목 길이 제한
                    platform = metadata.get('platform', 'youtube')
                    performance = metadata.get('performance_label', 'medium')
                    views = metadata.get('views', 0)
                    ownership = 'Own' if metadata.get('is_own_content', False) else 'Others'

                    meta_file.write(f"{title}\t{platform}\t{performance}\t{views}\t{ownership}\n")

            # 3. TensorBoard 설정 파일 생성
            self._create_projector_config()

            self.logger.info(f"Exported {len(all_vectors)} embeddings to {self.output_dir}")

            return str(self.output_dir)

    def _create_projector_config(self):
        """
        TensorBoard Projector 설정 파일 (projector_config.pbtxt)

        TensorBoard 실행:
        tensorboard --logdir=./embeddings_viz
        """
        config_path = self.output_dir / "projector_config.pbtxt"

        config_content = """
embeddings {
  tensor_name: "Thumbnail Embeddings"
  tensor_path: "embeddings.tsv"
  metadata_path: "metadata.tsv"
}
"""

        with open(config_path, 'w') as f:
            f.write(config_content.strip())

    def _create_dummy_visualization(self) -> str:
        """더미 데이터로 시각화 예제 생성"""
        # 100개 더미 벡터 (512차원)
        np.random.seed(42)

        # 클러스터 3개
        cluster1 = np.random.randn(30, 512) + [1, 0] + [0]*510  # 고성과
        cluster2 = np.random.randn(30, 512) + [0, 1] + [0]*510  # 중성과
        cluster3 = np.random.randn(40, 512) + [-1, -1] + [0]*510  # 저성과

        all_embeddings = np.vstack([cluster1, cluster2, cluster3])

        # TSV 저장
        embeddings_path = self.output_dir / "embeddings.tsv"
        metadata_path = self.output_dir / "metadata.tsv"

        with open(embeddings_path, 'w') as emb_file, \
             open(metadata_path, 'w') as meta_file:

            meta_file.write("Title\tPlatform\tPerformance\tViews\tOwnership\n")

            for i, vec in enumerate(all_embeddings):
                emb_file.write('\t'.join(map(str, vec)) + '\n')

                if i < 30:
                    meta_file.write(f"High Perf Video {i}\tyoutube\thigh\t150000\tOwn\n")
                elif i < 60:
                    meta_file.write(f"Medium Perf Video {i}\tfacebook\tmedium\t50000\tOwn\n")
                else:
                    meta_file.write(f"Others Video {i}\tinstagram\thigh\t200000\tOthers\n")

        self._create_projector_config()

        return str(self.output_dir)

    def generate_visualization_html(self) -> str:
        """
        임베딩 시각화 HTML 페이지 생성 (Plotly 사용)

        TensorBoard 대신 웹 브라우저에서 바로 볼 수 있는 대안
        """
        html_path = self.output_dir / "visualization.html"

        html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>OmniVibe Pro - Thumbnail Embeddings Visualization</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        #plot { width: 100%; height: 800px; }
        .info { background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <h1>📊 Thumbnail Embeddings Visualization</h1>

    <div class="info">
        <h3>시각화 가이드</h3>
        <ul>
            <li><strong>고성과 클러스터</strong>: 빨간색 포인트들이 모여있는 영역</li>
            <li><strong>자신의 컨텐츠</strong>: 원(●) 마커</li>
            <li><strong>타인의 컨텐츠</strong>: 별(★) 마커</li>
            <li><strong>인터랙션</strong>: 마우스로 드래그하여 회전, 줌 가능</li>
        </ul>
    </div>

    <div id="plot"></div>

    <script>
        // TODO: embeddings.tsv와 metadata.tsv 로드 후 Plotly로 시각화
        // 현재는 더미 데이터

        const trace1 = {
            x: [1, 2, 3, 4, 5],
            y: [1, 3, 2, 4, 3],
            mode: 'markers',
            type: 'scatter',
            name: 'High Performance (Own)',
            marker: { size: 12, color: 'red', symbol: 'circle' }
        };

        const trace2 = {
            x: [2, 3, 4, 5, 6],
            y: [3, 4, 2, 5, 4],
            mode: 'markers',
            type: 'scatter',
            name: 'High Performance (Others)',
            marker: { size: 12, color: 'orange', symbol: 'star' }
        };

        const layout = {
            title: 'Thumbnail Embeddings (t-SNE 2D)',
            xaxis: { title: 'Dimension 1' },
            yaxis: { title: 'Dimension 2' },
            hovermode: 'closest'
        };

        Plotly.newPlot('plot', [trace1, trace2], layout);
    </script>

    <div class="info" style="margin-top: 20px;">
        <h3>🎯 인사이트</h3>
        <p>TensorBoard 실행 방법:</p>
        <pre>cd backend
tensorboard --logdir=./embeddings_viz</pre>
        <p>그 다음 브라우저에서 <code>http://localhost:6006</code> 접속</p>
    </div>
</body>
</html>
"""

        with open(html_path, 'w') as f:
            f.write(html_content)

        self.logger.info(f"Created visualization HTML at {html_path}")
        return str(html_path)

    def analyze_clusters(self, embeddings: np.ndarray, metadata: List[Dict]) -> Dict:
        """
        임베딩 클러스터 분석 (K-means)

        Returns:
            클러스터별 성과 통계
        """
        from sklearn.cluster import KMeans

        # 3개 클러스터로 분류
        kmeans = KMeans(n_clusters=3, random_state=42)
        labels = kmeans.fit_predict(embeddings)

        cluster_stats = {}
        for cluster_id in range(3):
            cluster_indices = np.where(labels == cluster_id)[0]
            cluster_metadata = [metadata[i] for i in cluster_indices]

            avg_performance = np.mean([
                m.get('performance_score', 50) for m in cluster_metadata
            ])

            cluster_stats[f'Cluster {cluster_id}'] = {
                'size': len(cluster_indices),
                'avg_performance': avg_performance,
                'dominant_platform': self._most_common(
                    [m.get('platform', 'unknown') for m in cluster_metadata]
                )
            }

        return cluster_stats

    def _most_common(self, lst: List) -> str:
        """리스트에서 가장 빈번한 값"""
        if not lst:
            return "unknown"
        return max(set(lst), key=lst.count)
