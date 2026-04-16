// Configuración del Mapa Restringido
const map = L.map('map', { 
    zoomControl: false,
    attributionControl: false,
    minZoom: 5,        // No se aleja más de México
    maxZoom: 10,       // No se acerca demasiado para no perder contexto
    worldCopyJump: false,
    maxBounds: [[14.0, -118.0], [33.0, -86.0]] // Bloquea la cámara a México
}).setView([23.6345, -102.5528], 5);

L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    noWrap: true // EVITA QUE EL MAPA SE REPITA COMO UNA LÍNEA
}).addTo(map);

const initialView = [23.6345, -102.5528];
const initialZoom = 5;

// Función para cerrar y resetear zoom
function closePanel() {
    document.getElementById('side-panel').classList.remove('open');
    map.flyTo(initialView, initialZoom, { duration: 1.5 });
}

// Lógica de Interacción
// ... dentro de onEachFeature ...
layer.on('click', async (e) => {
    // 1. Zoom Inteligente al estado
    map.flyToBounds(layer.getBounds(), {
        padding: [50, 50], // Espacio para que no choque con los bordes
        maxZoom: 7,        // Nivel de zoom cómodo
        duration: 1.2
    });

    // 2. Abrir Panel
    document.getElementById('side-panel').classList.add('open');
    
    // ... (resto de las peticiones fetch igual que antes)
});

// Cerrar al hacer clic fuera (en el mapa base)
map.on('click', (e) => {
    if (e.originalEvent.target.id === 'map') {
        closePanel();
    }
});