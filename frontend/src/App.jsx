
import Admin from './Admin'
import PublicArtwork from './PublicArtwork'

function App() {
    const currentPath = window.location.pathname

    if (currentPath === '/admin') {
        return <Admin />
    }

    return <PublicArtwork />
}

export default App
