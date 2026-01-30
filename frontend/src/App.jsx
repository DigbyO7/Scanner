import React, { useState, useEffect } from 'react';
import { RefreshCw, TrendingUp, AlertCircle, Clock } from 'lucide-react';

function App() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetch('./data.json')
            .then(response => {
                if (!response.ok) throw new Error("Failed to load data");
                return response.json();
            })
            .then(result => {
                setData(result);
                setLoading(false);
            })
            .catch(err => {
                console.error("Error loading data.json:", err);
                // Fallback for demo purposes if file doesn't exist yet
                setError("Waiting for first scan...");
                setLoading(false);
            });
    }, []);

    if (loading) return (
        <div className="container" style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div className="loader"></div>
        </div>
    );

    return (
        <div className="container">
            <header>
                <div>
                    <h1>Camarilla Scanner</h1>
                    <p className="text-secondary text-sm">Identifying Tight CPR & Doji Setups</p>
                </div>
                <div className="flex items-center gap-2 text-sm text-secondary card" style={{ padding: '8px 16px', margin: 0 }}>
                    <Clock size={16} />
                    <span>Last Updated: {data ? data.last_updated : 'Never'}</span>
                </div>
            </header>

            {error && !data && (
                <div className="card flex items-center gap-2" style={{ borderColor: 'var(--accent-red)' }}>
                    <AlertCircle className="text-red" />
                    <p>No Data Available yet. Please wait for the daily scan to run.</p>
                </div>
            )}

            {data && data.stocks.length === 0 && (
                <div className="card flex items-center justify-center p-8">
                    <p className="text-secondary">No stocks matched the criteria today.</p>
                </div>
            )}

            <div className="grid">
                {data && data.stocks.map(stock => (
                    <StockCard key={stock.ticker} stock={stock} />
                ))}
            </div>

            <footer style={{ marginTop: '40px', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                <p>Automated by GitHub Actions | Updates daily at 6 PM IST</p>
            </footer>
        </div>
    );
}

function StockCard({ stock }) {
    return (
        <div className="card">
            <div className="flex justify-between items-center" style={{ marginBottom: '16px' }}>
                <h2 style={{ margin: 0, fontSize: '1.5rem' }}>{stock.ticker}</h2>
                <span className="badge badge-success">Buy Ready</span>
            </div>

            <div style={{ fontSize: '2rem', fontWeight: 'bold', marginBottom: '8px' }}>
                {stock.price}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginTop: '20px' }}>
                <div style={{ background: 'rgba(255,255,255,0.05)', padding: '10px', borderRadius: '8px' }}>
                    <div className="text-secondary text-sm">CPR Width</div>
                    <div className="font-bold text-blue">{stock.cpr.width_pct}%</div>
                </div>
                <div style={{ background: 'rgba(255,255,255,0.05)', padding: '10px', borderRadius: '8px' }}>
                    <div className="text-secondary text-sm">Camarilla Center</div>
                    <div className="font-bold text-green">{stock.camarilla.center}</div>
                </div>
            </div>

            <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                <div className="flex justify-between text-sm" style={{ marginBottom: '4px' }}>
                    <span className="text-secondary">Monthly Pivot</span>
                    <span>{stock.cpr.pivot}</span>
                </div>
                <div className="flex justify-between text-sm">
                    <span className="text-secondary">Daily Signal</span>
                    <span className="text-green flex items-center gap-2"><TrendingUp size={14} /> {stock.signal}</span>
                </div>
            </div>
        </div>
    )
}

export default App;
