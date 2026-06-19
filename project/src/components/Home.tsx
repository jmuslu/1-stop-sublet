import { useMemo, useState } from 'react';
import type { Listing } from '../types/listing';
import { isNortheastern } from '../utils/northeastern';

interface HomeProps {
  listings: Listing[];
  onBrowse: () => void;
}

function Home({ listings, onBrowse }: HomeProps) {
  const [showListModal, setShowListModal] = useState(false);

  const stats = useMemo(() => {
    const sources = new Set(listings.map((listing) => listing.platform));
    const verified = listings.filter((listing) => listing.sourceVettedUsers).length;
    const northeastern = listings.filter(isNortheastern).length;
    return {
      total: listings.length,
      sources: sources.size,
      verified,
      northeastern,
    };
  }, [listings]);

  return (
    <main className="home">
      <section className="hero">
        <p className="hero-eyebrow">For the Northeastern community</p>
        <h1 className="hero-title">Every Boston-area sublet, in one place.</h1>
        <p className="hero-mission">
          1StopSublet gathers short-term sublets from across the web and ranks them for
          Northeastern students — so you can find a safe, simple place to live without
          checking ten different sites.
        </p>
        <div className="hero-actions">
          <button className="btn btn-primary" onClick={onBrowse}>
            Find a Sublet
          </button>
          <button className="btn btn-secondary" onClick={() => setShowListModal(true)}>
            List Your Sublet
          </button>
        </div>

        <dl className="hero-stats">
          <div className="stat">
            <dt>{stats.total}</dt>
            <dd>live sublets</dd>
          </div>
          <div className="stat">
            <dt>{stats.sources}</dt>
            <dd>sources, one feed</dd>
          </div>
          <div className="stat">
            <dt>{stats.northeastern}</dt>
            <dd>near Northeastern</dd>
          </div>
          <div className="stat">
            <dt>{stats.verified}</dt>
            <dd>verified-student listings</dd>
          </div>
        </dl>
      </section>

      <section className="home-section">
        <h2 className="home-section-title">How it works</h2>
        <div className="card-row">
          <article className="info-card">
            <h3>We gather</h3>
            <p>
              We pull active sublets from verified-student platforms and community boards
              and standardize them into one consistent, scannable feed.
            </p>
          </article>
          <article className="info-card">
            <h3>We rank for NU</h3>
            <p>
              Listings on or near campus and from the Northeastern community rise to the
              top, so the most relevant options come first.
            </p>
          </article>
          <article className="info-card">
            <h3>We flag trust</h3>
            <p>
              Every listing shows where it came from and whether the source verifies its
              users, so you always know what you are looking at.
            </p>
          </article>
        </div>
      </section>

      <section className="home-section trust-section">
        <h2 className="home-section-title">Know who you are renting from</h2>
        <p className="home-section-lead">
          Not every listing is equal. We label each one by how much its source vets the
          people posting it.
        </p>
        <div className="card-row">
          <article className="info-card">
            <span className="trust-badge trust-verified">Verified student</span>
            <p>
              From platforms that require a student account to post, like SBLT and
              Subletr. The lister is a confirmed student.
            </p>
          </article>
          <article className="info-card">
            <span className="trust-badge trust-official">Official portal</span>
            <p>
              From Northeastern&rsquo;s own off-campus housing portal — an official
              channel, though not peer-verified.
            </p>
          </article>
          <article className="info-card">
            <span className="trust-badge trust-unverified">Community post</span>
            <p>
              From open boards like Reddit. Useful leads, but the poster is not verified —
              meet safely and confirm details.
            </p>
          </article>
        </div>
      </section>

      <section className="home-cta">
        <h2>Ready to find your next place?</h2>
        <button className="btn btn-primary" onClick={onBrowse}>
          Browse {stats.total} sublets
        </button>
      </section>

      {showListModal && (
        <div
          className="modal-overlay"
          role="dialog"
          aria-modal="true"
          aria-labelledby="list-modal-title"
          onClick={() => setShowListModal(false)}
        >
          <div className="modal" onClick={(event) => event.stopPropagation()}>
            <button
              className="modal-close"
              onClick={() => setShowListModal(false)}
              aria-label="Close"
            >
              &times;
            </button>
            <h2 id="list-modal-title">List your sublet</h2>
            <p>
              Posting directly on 1StopSublet is coming soon. For now, post on one of our
              verified-student partners and your listing will show up here automatically:
            </p>
            <div className="modal-actions">
              <a
                className="btn btn-primary"
                href="https://www.sblt.app"
                target="_blank"
                rel="noreferrer"
              >
                Post on SBLT
              </a>
              <a
                className="btn btn-secondary"
                href="https://www.subletr.com"
                target="_blank"
                rel="noreferrer"
              >
                Post on Subletr
              </a>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}

export default Home;
