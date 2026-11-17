
import { useEffect, useState } from 'react'
import './Admin.css'

const API_URL = import.meta.env.VITE_API_URL || ''

async function apiRequest(url, options = {}) {
    const response = await fetch(`${API_URL}${url}`, options)

    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
        throw new Error(data.detail || 'Ошибка запроса')
    }

    return data
}

function Admin() {
    const [section, setSection] = useState('artworks')
    const [artworks, setArtworks] = useState([])
    const [tracks, setTracks] = useState([])
    const [recommendations, setRecommendations] = useState([])

    const [selectedArtwork, setSelectedArtwork] = useState('')
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')
    const [message, setMessage] = useState('')

    const [editingArtwork, setEditingArtwork] = useState(null)
    const [artworkForm, setArtworkForm] = useState({
        title: '',
        artist: '',
        year: '',
        description: ''
    })

    const [editingTrack, setEditingTrack] = useState(null)
    const [trackForm, setTrackForm] = useState({
        title: '',
        artist: '',
        license_name: '',
        license_url: '',
        allowed_public_playback: false,
        is_active: true
    })

    async function loadData() {
        try {
            setLoading(true)
            setError('')

            const [artworkData, trackData] = await Promise.all([
                apiRequest('/artworks'),
                apiRequest('/tracks')
            ])

            setArtworks(artworkData)
            setTracks(trackData)

            if (artworkData.length > 0 && !selectedArtwork) {
                setSelectedArtwork(String(artworkData[0].id))
            }
        } catch (error) {
            setError(error.message)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        loadData()
    }, [])

    useEffect(() => {
        if (!selectedArtwork) {
            setRecommendations([])
            return
        }

        async function loadRecommendations() {
            try {
                const data = await apiRequest(
                    `/artworks/${selectedArtwork}/recommendations`
                )

                setRecommendations(data)
            } catch (error) {
                setError(error.message)
            }
        }

        loadRecommendations()
    }, [selectedArtwork])

    async function uploadArtwork(event) {
        event.preventDefault()

        const formData = new FormData(event.target)

        setError('')
        setMessage('')

        try {
            await apiRequest('/artworks', {
                method: 'POST',
                body: formData
            })

            setMessage('Картина успешно добавлена')
            event.target.reset()
            await loadData()
        } catch (error) {
            setError(error.message)
        }
    }

    async function uploadTrack(event) {
        event.preventDefault()

        const formData = new FormData(event.target)

        const allowed =
            formData.get('allowed_public_playback') === 'on'

        formData.set('allowed_public_playback', String(allowed))

        setError('')
        setMessage('')

        try {
            await apiRequest('/tracks', {
                method: 'POST',
                body: formData
            })

            setMessage('Музыкальный трек успешно добавлен')
            event.target.reset()
            await loadData()
        } catch (error) {
            setError(error.message)
        }
    }

    function startArtworkEditing(artwork) {
        setEditingArtwork(artwork.id)

        setArtworkForm({
            title: artwork.title || '',
            artist: artwork.artist || '',
            year: artwork.year ?? '',
            description: artwork.description || ''
        })

        setError('')
        setMessage('')
    }

    function cancelArtworkEditing() {
        setEditingArtwork(null)
    }

    async function saveArtwork(event) {
        event.preventDefault()

        try {
            setError('')
            setMessage('')

            await apiRequest(`/artworks/${editingArtwork}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    title: artworkForm.title,
                    artist: artworkForm.artist,
                    year: artworkForm.year === ''
                        ? null
                        : Number(artworkForm.year),
                    description: artworkForm.description
                })
            })

            setEditingArtwork(null)
            setMessage('Информация о картине обновлена')
            await loadData()
        } catch (error) {
            setError(error.message)
        }
    }

    function startTrackEditing(track) {
        setEditingTrack(track.id)

        setTrackForm({
            title: track.title || '',
            artist: track.artist || '',
            license_name: track.license_name || '',
            license_url: track.license_url || '',
            allowed_public_playback: track.allowed_public_playback,
            is_active: track.is_active
        })

        setError('')
        setMessage('')
    }

    function cancelTrackEditing() {
        setEditingTrack(null)
    }

    async function saveTrack(event) {
        event.preventDefault()

        try {
            setError('')
            setMessage('')

            await apiRequest(`/tracks/${editingTrack}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(trackForm)
            })

            setEditingTrack(null)
            setMessage('Информация о музыкальном треке обновлена')
            await loadData()
        } catch (error) {
            setError(error.message)
        }
    }

    async function generateRecommendations() {
        if (!selectedArtwork) return

        try {
            setError('')
            setMessage('')

            const data = await apiRequest(
                `/artworks/${selectedArtwork}/recommendations/generate`,
                { method: 'POST' }
            )

            setRecommendations(data)
            setMessage('Рекомендации успешно сформированы')
        } catch (error) {
            setError(error.message)
        }
    }

    async function reviewRecommendation(id, action) {
        try {
            setError('')
            setMessage('')

            await apiRequest(`/recommendations/${id}/${action}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ comment: null })
            })

            const data = await apiRequest(
                `/artworks/${selectedArtwork}/recommendations`
            )

            setRecommendations(data)

            setMessage(
                action === 'approve'
                    ? 'Рекомендация одобрена'
                    : 'Рекомендация отклонена'
            )
        } catch (error) {
            setError(error.message)
        }
    }

    async function updateTrack(id, field, value) {
        try {
            setError('')
            setMessage('')

            await apiRequest(`/tracks/${id}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ [field]: value })
            })

            await loadData()
            setMessage('Настройки трека обновлены')
        } catch (error) {
            setError(error.message)
        }
    }

    async function publishArtwork(id) {
        try {
            setError('')
            setMessage('')

            await apiRequest(`/artworks/${id}/publish`, {
                method: 'POST'
            })

            await loadData()
            setMessage('Картина опубликована')
        } catch (error) {
            setError(error.message)
        }
    }

    if (loading) {
        return <main className="admin-page">Загрузка...</main>
    }

    return (
        <main className="admin-page">
            <header className="admin-header">
                <a href="/" className="admin-logo">
                    ART<span>/</span>SOUND
                </a>

                <span>ПАНЕЛЬ АДМИНИСТРАТОРА</span>
            </header>

            <nav className="admin-nav">
                <button
                    className={section === 'artworks' ? 'active' : ''}
                    onClick={() => setSection('artworks')}
                >
                    Картины
                </button>

                <button
                    className={section === 'tracks' ? 'active' : ''}
                    onClick={() => setSection('tracks')}
                >
                    Музыка
                </button>

                <button
                    className={section === 'recommendations' ? 'active' : ''}
                    onClick={() => setSection('recommendations')}
                >
                    Рекомендации
                </button>
            </nav>

            {error && <p className="admin-error">{error}</p>}
            {message && <p className="admin-message">{message}</p>}

            {section === 'artworks' && (
                <section className="admin-content">
                    <h1>Картины</h1>

                    <form onSubmit={uploadArtwork} className="admin-form">
                        <h2>Добавить картину</h2>

                        <input
                            name="title"
                            placeholder="Название картины"
                            required
                        />

                        <input
                            name="artist"
                            placeholder="Автор"
                            required
                        />

                        <input
                            name="year"
                            type="number"
                            placeholder="Год создания"
                        />

                        <textarea
                            name="description"
                            placeholder="Описание картины"
                        />

                        <label>Изображение картины</label>

                        <input
                            name="image"
                            type="file"
                            accept=".jpg,.jpeg,.png,.webp"
                            required
                        />

                        <button type="submit">Загрузить картину</button>
                    </form>

                    <h2>Загруженные картины</h2>

                    <div className="admin-list">
                        {artworks.map(artwork => (
                            <article className="admin-item" key={artwork.id}>
                                <div>
                                    <h3>{artwork.title}</h3>
                                    <p>{artwork.artist}</p>
                                    <p>ID: {artwork.id}</p>
                                    <p>Статус: {artwork.status}</p>
                                    {artwork.year && (
                                        <p>Год: {artwork.year}</p>
                                    )}
                                </div>

                                <div className="admin-actions">
                                    <button
                                        onClick={() =>
                                            startArtworkEditing(artwork)
                                        }
                                    >
                                        Редактировать
                                    </button>

                                    {artwork.status !== 'published' && (
                                        <button
                                            onClick={() =>
                                                publishArtwork(artwork.id)
                                            }
                                        >
                                            Опубликовать
                                        </button>
                                    )}

                                    <a
                                        href={`${API_URL}/artworks/${artwork.id}/qr`}
                                        target="_blank"
                                        rel="noreferrer"
                                    >
                                        QR-код
                                    </a>
                                </div>

                                {editingArtwork === artwork.id && (
                                    <form
                                        className="admin-form admin-edit-form"
                                        onSubmit={saveArtwork}
                                    >
                                        <h3>Редактирование картины</h3>

                                        <input
                                            value={artworkForm.title}
                                            onChange={event =>
                                                setArtworkForm({
                                                    ...artworkForm,
                                                    title: event.target.value
                                                })
                                            }
                                            placeholder="Название картины"
                                            required
                                        />

                                        <input
                                            value={artworkForm.artist}
                                            onChange={event =>
                                                setArtworkForm({
                                                    ...artworkForm,
                                                    artist: event.target.value
                                                })
                                            }
                                            placeholder="Автор"
                                            required
                                        />

                                        <input
                                            type="number"
                                            value={artworkForm.year}
                                            onChange={event =>
                                                setArtworkForm({
                                                    ...artworkForm,
                                                    year: event.target.value
                                                })
                                            }
                                            placeholder="Год создания"
                                        />

                                        <textarea
                                            value={artworkForm.description}
                                            onChange={event =>
                                                setArtworkForm({
                                                    ...artworkForm,
                                                    description: event.target.value
                                                })
                                            }
                                            placeholder="Описание картины"
                                        />

                                        <div className="admin-actions">
                                            <button type="submit">
                                                Сохранить
                                            </button>

                                            <button
                                                type="button"
                                                className="reject-button"
                                                onClick={cancelArtworkEditing}
                                            >
                                                Отмена
                                            </button>
                                        </div>
                                    </form>
                                )}
                            </article>
                        ))}

                        {artworks.length === 0 && (
                            <p>Картин пока нет</p>
                        )}
                    </div>
                </section>
            )}

            {section === 'tracks' && (
                <section className="admin-content">
                    <h1>Музыкальные треки</h1>

                    <form onSubmit={uploadTrack} className="admin-form">
                        <h2>Добавить музыку</h2>

                        <input
                            name="title"
                            placeholder="Название композиции"
                            required
                        />

                        <input
                            name="artist"
                            placeholder="Исполнитель"
                        />

                        <input
                            name="license_name"
                            placeholder="Название лицензии"
                        />

                        <input
                            name="license_url"
                            type="url"
                            placeholder="Ссылка на лицензию"
                        />

                        <label className="admin-checkbox">
                            <input
                                name="allowed_public_playback"
                                type="checkbox"
                            />
                            Разрешено публичное воспроизведение
                        </label>

                        <label>Аудиофайл</label>

                        <input
                            name="audio"
                            type="file"
                            accept=".mp3,.wav,.ogg,.flac"
                            required
                        />

                        <button type="submit">Загрузить музыку</button>

                        <p className="admin-note">
                            Отмечайте разрешение на публичное воспроизведение
                            только после проверки прав на композицию.
                        </p>
                    </form>

                    <h2>Загруженные треки</h2>

                    <div className="admin-list">
                        {tracks.map(track => (
                            <article className="admin-item" key={track.id}>
                                <div>
                                    <h3>{track.title}</h3>

                                    <p>
                                        {track.artist || 'Исполнитель неизвестен'}
                                    </p>

                                    <p>ID: {track.id}</p>

                                    <p>
                                        Длительность: {track.duration_sec} сек.
                                    </p>

                                    <p>
                                        Лицензия: {track.license_name || 'Не указана'}
                                    </p>
                                </div>

                                <div className="admin-track-settings">
                                    <label>
                                        <input
                                            type="checkbox"
                                            checked={track.is_active}
                                            onChange={event =>
                                                updateTrack(
                                                    track.id,
                                                    'is_active',
                                                    event.target.checked
                                                )
                                            }
                                        />
                                        Активен
                                    </label>

                                    <label>
                                        <input
                                            type="checkbox"
                                            checked={track.allowed_public_playback}
                                            onChange={event =>
                                                updateTrack(
                                                    track.id,
                                                    'allowed_public_playback',
                                                    event.target.checked
                                                )
                                            }
                                        />
                                        Публичное воспроизведение разрешено
                                    </label>

                                    <button
                                        onClick={() =>
                                            startTrackEditing(track)
                                        }
                                    >
                                        Редактировать
                                    </button>
                                </div>

                                {editingTrack === track.id && (
                                    <form
                                        className="admin-form admin-edit-form"
                                        onSubmit={saveTrack}
                                    >
                                        <h3>Редактирование трека</h3>

                                        <input
                                            value={trackForm.title}
                                            onChange={event =>
                                                setTrackForm({
                                                    ...trackForm,
                                                    title: event.target.value
                                                })
                                            }
                                            placeholder="Название композиции"
                                            required
                                        />

                                        <input
                                            value={trackForm.artist}
                                            onChange={event =>
                                                setTrackForm({
                                                    ...trackForm,
                                                    artist: event.target.value
                                                })
                                            }
                                            placeholder="Исполнитель"
                                        />

                                        <input
                                            value={trackForm.license_name}
                                            onChange={event =>
                                                setTrackForm({
                                                    ...trackForm,
                                                    license_name: event.target.value
                                                })
                                            }
                                            placeholder="Название лицензии"
                                        />

                                        <input
                                            type="url"
                                            value={trackForm.license_url}
                                            onChange={event =>
                                                setTrackForm({
                                                    ...trackForm,
                                                    license_url: event.target.value
                                                })
                                            }
                                            placeholder="Ссылка на лицензию"
                                        />

                                        <label className="admin-checkbox">
                                            <input
                                                type="checkbox"
                                                checked={trackForm.allowed_public_playback}
                                                onChange={event =>
                                                    setTrackForm({
                                                        ...trackForm,
                                                        allowed_public_playback: event.target.checked
                                                    })
                                                }
                                            />
                                            Разрешено публичное воспроизведение
                                        </label>

                                        <label className="admin-checkbox">
                                            <input
                                                type="checkbox"
                                                checked={trackForm.is_active}
                                                onChange={event =>
                                                    setTrackForm({
                                                        ...trackForm,
                                                        is_active: event.target.checked
                                                    })
                                                }
                                            />
                                            Трек активен
                                        </label>

                                        <div className="admin-actions">
                                            <button type="submit">
                                                Сохранить
                                            </button>

                                            <button
                                                type="button"
                                                className="reject-button"
                                                onClick={cancelTrackEditing}
                                            >
                                                Отмена
                                            </button>
                                        </div>
                                    </form>
                                )}
                            </article>
                        ))}

                        {tracks.length === 0 && (
                            <p>Музыкальных треков пока нет</p>
                        )}
                    </div>
                </section>
            )}

            {section === 'recommendations' && (
                <section className="admin-content">
                    <h1>Музыкальные рекомендации</h1>

                    <label>Выберите картину</label>

                    <select
                        value={selectedArtwork}
                        onChange={event =>
                            setSelectedArtwork(event.target.value)
                        }
                    >
                        <option value="">Выберите картину</option>

                        {artworks.map(artwork => (
                            <option
                                key={artwork.id}
                                value={artwork.id}
                            >
                                {artwork.title}
                            </option>
                        ))}
                    </select>

                    <button
                        onClick={generateRecommendations}
                        disabled={!selectedArtwork}
                    >
                        Сформировать рекомендации
                    </button>

                    <div className="admin-list">
                        {recommendations.map(item => (
                            <article className="admin-item" key={item.id}>
                                <div>
                                    <h3>{item.track.title}</h3>

                                    <p>
                                        {item.track.artist || 'Исполнитель неизвестен'}
                                    </p>

                                    <p>
                                        Совместимость: {item.score} / 100
                                    </p>

                                    <p>Статус: {item.status}</p>

                                    <p>
                                        Версия алгоритма: {item.algorithm_version}
                                    </p>
                                </div>

                                <div className="admin-actions">
                                    {item.status !== 'approved' && (
                                        <button
                                            onClick={() =>
                                                reviewRecommendation(
                                                    item.id,
                                                    'approve'
                                                )
                                            }
                                        >
                                            Одобрить
                                        </button>
                                    )}

                                    {item.status !== 'rejected' && (
                                        <button
                                            className="reject-button"
                                            onClick={() =>
                                                reviewRecommendation(
                                                    item.id,
                                                    'reject'
                                                )
                                            }
                                        >
                                            Отклонить
                                        </button>
                                    )}
                                </div>
                            </article>
                        ))}

                        {selectedArtwork && recommendations.length === 0 && (
                            <p>Рекомендаций пока нет</p>
                        )}
                    </div>
                </section>
            )}
        </main>
    )
}

export default Admin
