"use client";

import { useEffect, useRef } from "react";
import maplibregl, {
  type Map as MLMap,
  type Marker as MLMarker,
} from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

export interface MapMarker {
  id: string;
  lat: number;
  lng: number;
  color?: string;
  label?: string;
  onClick?: () => void;
}

const ISSUE_COLORS: Record<string, string> = {
  pothole: "#1d58e3",
  garbage: "#f98307",
  damaged_streetlight: "#9333ea",
  waterlogging: "#0891b2",
  illegal_dumping: "#dc2626",
};

export function markerColor(issueType?: string | null): string {
  return ISSUE_COLORS[issueType ?? ""] ?? "#4a5368";
}

const OSM_STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: {
    osm: {
      type: "raster",
      tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
      tileSize: 256,
      maxzoom: 19,
      attribution: "© OpenStreetMap contributors",
    },
  },
  layers: [{ id: "osm", type: "raster", source: "osm" }],
};

interface MapViewProps {
  center?: [number, number];
  zoom?: number;
  markers?: MapMarker[];
  onMapClick?: (lat: number, lng: number) => void;
  interactive?: boolean;
  className?: string;
  fitToMarkers?: boolean;
}

export default function MapView({
  center = [73.02, 19.05],
  zoom = 11,
  markers = [],
  onMapClick,
  interactive = true,
  className = "h-96 w-full",
  fitToMarkers = false,
}: MapViewProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MLMap | null>(null);
  const markersRef = useRef<Record<string, MLMarker>>({});
  const clickRef = useRef(onMapClick);
  const markersRefData = useRef(markers);

  clickRef.current = onMapClick;
  markersRefData.current = markers;

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: OSM_STYLE,
      center,
      zoom,
      interactive,
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    if (onMapClick) {
      map.on("click", (e) => {
        clickRef.current?.(e.lngLat.lat, e.lngLat.lng);
      });
    }
    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
      markersRef.current = {};
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Sync markers
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const nextIds = new Set(markers.map((m) => m.id));
    for (const [id, marker] of Object.entries(markersRef.current)) {
      if (!nextIds.has(id)) {
        marker.remove();
        delete markersRef.current[id];
      }
    }

    for (const m of markers) {
      const el = document.createElement("button");
      el.type = "button";
      el.setAttribute("aria-label", m.label || "Map marker");
      el.style.cssText = `display:flex;align-items:center;justify-content:center;
        width:26px;height:26px;border-radius:50% 50% 50% 0;transform:rotate(-45deg);
        background:${m.color ?? markerColor()};border:2px solid white;
        box-shadow:0 1px 4px rgba(0,0,0,.4);cursor:pointer;padding:0;`;
      const dot = document.createElement("span");
      dot.style.cssText = "width:8px;height:8px;border-radius:50%;background:white;transform:rotate(45deg);";
      el.appendChild(dot);
      el.addEventListener("click", (ev) => {
        ev.stopPropagation();
        m.onClick?.();
      });

      const existing = markersRef.current[m.id];
      const lngLat: [number, number] = [m.lng, m.lat];
      if (existing) {
        existing.setLngLat(lngLat);
        existing.getElement().replaceWith(el);
      } else {
        markersRef.current[m.id] = new maplibregl.Marker({ element: el })
          .setLngLat(lngLat)
          .addTo(map);
      }
    }

    if (fitToMarkers && markers.length > 0) {
      const bounds = new maplibregl.LngLatBounds();
      markers.forEach((m) => bounds.extend([m.lng, m.lat]));
      map.fitBounds(bounds, { padding: 48, maxZoom: 15, duration: 400 });
    }
  }, [markers, fitToMarkers]);

  return <div ref={containerRef} className={className} aria-label="Map" />;
}
