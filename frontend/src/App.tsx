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
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const getCoverUrl = (coverId: number | null) => {
    if (!coverId) {
      return null;
    }

    return `https://covers.openlibrary.org/b/id/${coverId}-L.jpg`;
  };

  const discoverBooks = async () => {
    const trimmedQuery = query.trim();

    if (!trimmedQuery || loading) {
      return;
    }

    setLoading(true);
    setError("");
    setSubmittedQuery(trimmedQuery);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/books/recommend",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            query: trimmedQuery,
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
      setError(
        "BookWise couldn't generate recommendations. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (
    event: React.KeyboardEvent<HTMLTextAreaElement>
  ) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      discoverBooks();
    }
  };

  return (
    <main className="app-shell">
      <section className="bookwise-dashboard">

        {/* LEFT PANEL */}

        <aside className="assistant-panel">
          <header className="brand-header">
            <div className="brand-mark">B</div>

            <div>
              <div className="brand-name">
                BookWise <span>AI</span>
              </div>
              <div className="brand-subtitle">
                Intelligent book discovery
              </div>
            </div>
          </header>

          <div className="conversation">
            {!submittedQuery && (
              <div className="welcome">
                <div className="welcome-icon">✦</div>

                <h1>What do you want to read?</h1>

                <p>
                  Describe a mood, story, character, setting, or idea.
                  BookWise will find books that match what you're looking for.
                </p>

                <div className="suggestions">
                  <button
                    onClick={() =>
                      setQuery(
                        "A mysterious adventure for a child who likes space"
                      )
                    }
                  >
                    Mysterious space adventure
                  </button>

                  <button
                    onClick={() =>
                      setQuery(
                        "A magical fantasy story full of adventure"
                      )
                    }
                  >
                    Magical fantasy
                  </button>

                  <button
                    onClick={() =>
                      setQuery(
                        "A cozy reflective story for a rainy afternoon"
                      )
                    }
                  >
                    Cozy rainy-day read
                  </button>
                </div>
              </div>
            )}

            {submittedQuery && (
              <>
                <div className="message user-message">
                  <span className="message-label">YOU</span>
                  <p>{submittedQuery}</p>
                </div>

                {!loading && recommendations.length > 0 && (
                  <div className="assistant-message-row">
                    <div className="ai-avatar">AI</div>

                    <div className="message ai-message">
                      <span className="message-label">BOOKWISE</span>
                      <p>
                        I found {recommendations.length} books that match
                        what you're looking for. I ranked them using semantic
                        similarity and AI reranking.
                      </p>
                    </div>
                  </div>
                )}

                {loading && (
                  <div className="assistant-message-row">
                    <div className="ai-avatar">AI</div>

                    <div className="message ai-message">
                      <div className="thinking">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>

                      <p className="thinking-text">
                        Searching and ranking books...
                      </p>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          <div className="composer-wrapper">
            {error && <div className="error-message">{error}</div>}

            <div className="composer">
              <textarea
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Describe your mood or what you'd like to read..."
                rows={2}
              />

              <button
                className="send-button"
                onClick={discoverBooks}
                disabled={loading || !query.trim()}
                aria-label="Discover books"
              >
                {loading ? "•••" : "➜"}
              </button>
            </div>

            <div className="composer-hint">
              Press Enter to discover · Shift + Enter for a new line
            </div>
          </div>
        </aside>

        {/* RIGHT PANEL */}

        <section className="recommendations-panel">
          <header className="recommendations-header">
            <div>
              <p className="section-eyebrow">PERSONALIZED FOR YOU</p>
              <h2>Your Curated Recommendations</h2>
            </div>

            <div className="match-count">
              {recommendations.length}{" "}
              {recommendations.length === 1 ? "match" : "matches"}
            </div>
          </header>

          {!submittedQuery && (
            <div className="empty-state">
              <div className="empty-symbol">✦</div>
              <h3>Your next great read starts here.</h3>
              <p>
                Tell BookWise what you're in the mood for and your
                recommendations will appear here.
              </p>
            </div>
          )}

          {loading && (
            <div className="results-loading">
              <div className="large-spinner"></div>
              <h3>Curating your bookshelf</h3>
              <p>
                Searching by meaning, then asking AI to rank the best matches.
              </p>
            </div>
          )}

          {!loading && recommendations.length > 0 && (
            <div className="recommendation-grid">
              {recommendations.map((book, index) => {
                const coverUrl = getCoverUrl(book.cover_id);

                return (
                  <article className="book-card" key={book.id}>
                    <div className="cover-container">
                      <div className="ranking-badge">
                        #{index + 1}
                      </div>

                      {coverUrl ? (
                        <img
                          src={coverUrl}
                          alt={`Cover of ${book.title}`}
                          className="book-cover"
                        />
                      ) : (
                        <div className="book-cover cover-fallback">
                          <span>BookWise</span>
                          <strong>{book.title}</strong>
                        </div>
                      )}
                    </div>

                    <div className="book-info">
                      <div className="score-row">
                        <span className="ai-match">
                          {Math.round(book.score * 100)}% AI Match
                        </span>
                      </div>

                      <h3>{book.title}</h3>

                      <p className="book-author">
                        {book.authors.length > 0
                          ? book.authors.join(", ")
                          : "Unknown author"}
                      </p>

                      {book.description && (
                        <p className="book-description">
                          {book.description}
                        </p>
                      )}

                      <div className="reason-box">
                        <span>WHY YOU'LL LIKE THIS</span>
                        <p>{book.reason}</p>
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </section>
      </section>
    </main>
  );
}

export default App;