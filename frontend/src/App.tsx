import { useState } from "react";
import "./App.css";

interface Recommendation {
  id: string;
  title: string;
  authors: string[];
  description: string | null;
  cover_id: number | null;
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

  const getCoverUrl = (coverId: number | null) => {
    if (!coverId) {
      return null;
    }

    return `https://covers.openlibrary.org/b/id/${coverId}-M.jpg`;
  };

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
        },
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
          Describe what you're in the mood for and let AI find books that match.
        </p>

        <div className="search-box">
          <textarea
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Try: A mysterious space adventure for a child..."
            rows={3}
          />

          <button onClick={discoverBooks} disabled={loading}>
            {loading ? "Finding books..." : "Discover books"}
          </button>
        </div>

        {error && <p className="error">{error}</p>}
      </section>

      {loading && (
        <section className="loading-section">
          <div className="spinner" />
          <h2>Finding your books...</h2>
          <p>BookWise is searching and reranking the best matches for you.</p>
        </section>
      )}

      {!loading && recommendations.length > 0 && (
        <section className="results">
          <div className="results-header">
            <p className="eyebrow">AI recommendations</p>
            <h2>Recommended for you</h2>
          </div>

          <div className="book-grid">
            {recommendations.map((book, index) => {
              const coverUrl = getCoverUrl(book.cover_id);

              return (
                <article className="book-card" key={book.id}>
                  <div className="book-cover">
                    {coverUrl ? (
                      <img src={coverUrl} alt={`Cover of ${book.title}`} />
                    ) : (
                      <div className="cover-placeholder">No cover</div>
                    )}
                  </div>

                  <div className="book-content">
                    <div className="rank">#{index + 1}</div>

                    <h3>{book.title}</h3>

                    {book.authors.length > 0 && (
                      <p className="authors">{book.authors.join(", ")}</p>
                    )}

                    <div className="match">
                      {Math.round(book.score * 100)}% AI match
                    </div>

                    {book.description && (
                      <p className="description">{book.description}</p>
                    )}

                    <div className="why">
                      <strong>Why BookWise recommends it</strong>
                      <p>{book.reason}</p>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        </section>
      )}
    </main>
  );
}

export default App;
