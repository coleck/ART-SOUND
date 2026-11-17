
import { useEffect, useState } from 'react'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || ''

const QR_TOKEN = new URLSearchParams(
    window.location.search
).get('token')

function PublicArtwork() {
    const [artwork, setArtwork] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')

    useEffect(() => {
        async function loadArtwork() {
            if (!QR_TOKEN) {
                setError('QR-токен не указан в адресе страницы')
                setLoading(false)
                return
            }

            try {
                const response = await fetch(
                    `${API_URL}/public/artworks/${QR_TOKEN}`
                )

                if (!response.ok) {
                    const data = await response.json()
                    throw new Error(
                        data.detail || 'Не удалось загрузить картину'
                    )
                }

                const data = await response.json()
                setArtwork(data)

            } catch (error) {
                setError(error.message)
            } finally {
                setLoading(false)
            }
        }

        loadArtwork()
    }, [])

    if (loading) {
        return (
            <main className="message">
                Загрузка картины...
            </main>
        )
    }

    if (error) {
        return (
            <main className="message">
                Ошибка: {error}
            </main>
        )
    }

    if (!artwork || !artwork.artwork || !artwork.music) {
        return (
            <main className="message">
                Картина или музыкальное сопровождение не найдены
            </main>
        )
    }

    const painting = artwork.artwork
    const music = artwork.music

    const imageUrl =
        `${API_URL}/public/artworks/${QR_TOKEN}/image`

    const audioUrl =
        `${API_URL}/public/artworks/${QR_TOKEN}/audio`

    return (
        <main className="page">
            <header className="header">
                <a href="#" className="logo">
                    ART<span>/</span>SOUND
                </a>

                <span className="header-label">
                    DIGITAL GALLERY
                </span>
            </header>

            <section className="artwork-section">
                <div className="artwork-image">
                    <img
                        src={imageUrl}
                        alt={painting.title}
                    />

                    <span className="image-number">
                        ARTWORK № {painting.id}
                    </span>
                </div>

                <div className="artwork-info">
                    <span className="eyebrow">
                        ИСКУССТВО И ЗВУК
                    </span>

                    <h1>{painting.title}</h1>

                    <div className="artwork-meta">
                        <span>
                            {painting.artist || 'Автор неизвестен'}
                        </span>

                        {painting.year && (
                            <>
                                <span className="meta-divider">/</span>
                                <span>{painting.year}</span>
                            </>
                        )}
                    </div>

                    {painting.description && (
                        <div className="description">
                            <h2>О произведении</h2>
                            <p>{painting.description}</p>
                        </div>
                    )}

                    <div className="music-section">
                        <span className="eyebrow">
                            МУЗЫКАЛЬНОЕ СОПРОВОЖДЕНИЕ
                        </span>

                        <div className="music-card">
                            <div className="music-cover">
                                <span>♪</span>
                            </div>

                            <div className="music-info">
                                <h3>{music.title}</h3>
                                <p>
                                    {music.artist || 'Исполнитель неизвестен'}
                                </p>
                            </div>
                        </div>

                        <audio
                            className="audio-player"
                            controls
                            preload="metadata"
                        >
                            <source
                                src={audioUrl}
                                type="audio/mpeg"
                            />
                            Ваш браузер не поддерживает аудио.
                        </audio>

                        <p className="music-score">
                            Совместимость по алгоритму: {music.score} / 100
                        </p>
                    </div>
                </div>
            </section>

            <footer className="footer">
                <span>ART / SOUND</span>
                <span>
                    ИСКУССТВО, КОТОРОЕ МОЖНО УСЛЫШАТЬ
                </span>
            </footer>
        </main>
    )
}

export default PublicArtwork
