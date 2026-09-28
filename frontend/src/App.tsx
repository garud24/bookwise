import { useState } from "react";
import "./App.css";

interface Recommendation {
  id: string;
  title: string;
  score: number;
  reason: string;
}

interface RecommendationResponse {
  query: string;
  recommendations: Recommendation[];
}

function App() {
  const [query, setQuery] = useState("");
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const discoverBooks = async () => {
    if (!query.trim()) {
      setError("Tell BookWise what kind of book you're looking for.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/books/recommend",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            query,
            max_results: 5,
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Unable to get recommendations.");
      }

      const data: RecommendationResponse = await response.json();

      setRecommendations(data.recommendations);
    } catch (err) {
      console.error(err);
      setError("Something went wrong while finding books.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="app">
      <section className="hero">
        <div className="brand">BookWise</div>

        <h1>Find your next great read.</h1>

        <p className="subtitle">
          Describe what you're in the mood for and let AI find books
          that match.
        </p>

        <div className="search-box">
          <textarea
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Try: A mysterious space adventure for a child..."
            rows={3}
          />

          <button
            onClick={discoverBooks}
            disabled={loading}
          >
            {loading ? "Finding books..." : "Discover books"}
          </button>
        </div>

        {error && <p className="error">{error}</p>}
      </section>

      {loading && (
        <section className="loading-section">
          <div className="spinner" />
          <h2>Finding your books...</h2>
          <p>
            BookWise is searching and reranking the best matches for you.
          </p>
        </section>
      )}

      {!loading && recommendations.length > 0 && (
        <section className="results">
          <div className="results-header">
            <p className="eyebrow">AI recommendations</p>
            <h2>Recommended for you</h2>
          </div>

          <div className="book-grid">
            {recommendations.map((book, index) => (
              <article className="book-card" key={book.id}>
                <div className="rank">#{index + 1}</div>

                <h3>{book.title}</h3>

                <div className="match">
                  {Math.round(book.score * 100)}% match
                </div>

                <p>{book.reason}</p>
              </article>
            ))}
          </div>
        </section>
      )}
    </main>
  );
}

export default App;