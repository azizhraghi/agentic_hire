# -*- coding: utf-8 -*-
"""
Map Generator — Génère une carte interactive Folium avec les startups matchées.
"""
import folium
from folium.plugins import MarkerCluster
from typing import List, Optional
from models import MatchResult, UserStartupInput


class MapGenerator:
    """Génère des cartes interactives avec Folium."""

    # Color mapping based on match score
    COLORS = {
        "high": "#22c55e",      # Green ≥75%
        "medium": "#eab308",    # Yellow 50-74%
        "low": "#ef4444",       # Red <50%
    }

    ICONS = {
        "high": "star",
        "medium": "info-sign",
        "low": "map-marker",
    }

    def _get_score_tier(self, score: float) -> str:
        if score >= 75:
            return "high"
        elif score >= 50:
            return "medium"
        return "low"

    def _format_revenue(self, amount: float) -> str:
        if amount >= 1_000_000:
            return f"${amount / 1_000_000:.1f}M"
        elif amount >= 1_000:
            return f"${amount / 1_000:.0f}K"
        return f"${amount:,.0f}"

    def generate_competitor_map(
        self,
        matches: List[MatchResult],
        user_input: Optional[UserStartupInput] = None,
        zoom_start: int = 4,
    ) -> folium.Map:
        """
        Génère une carte interactive avec les startups matchées.
        
        Args:
            matches: Liste des résultats de matching
            user_input: Profil utilisateur (pour le marqueur tunisien)
            zoom_start: Niveau de zoom initial
            
        Returns:
            Objet folium.Map
        """
        # Center on US by default
        center_lat = 39.8283
        center_lng = -98.5795

        m = folium.Map(
            location=[center_lat, center_lng],
            zoom_start=zoom_start,
            tiles="CartoDB dark_matter",
            attr="StartupMatch AI"
        )

        # Add marker cluster for US startups
        cluster = MarkerCluster(
            name="Startups US similaires",
            options={
                "maxClusterRadius": 50,
                "spiderfyDistanceMultiplier": 2,
            }
        )

        for match in matches:
            ref = match.reference_startup
            tier = self._get_score_tier(match.similarity_score)
            color = self.COLORS[tier]
            icon_name = self.ICONS[tier]

            # Build popup HTML
            popup_html = f"""
            <div style="font-family: 'Inter', Arial, sans-serif; max-width: 280px; padding: 8px;">
                <h4 style="margin: 0 0 8px; color: #1e1b4b; font-size: 15px;">
                    🚀 {ref.name}
                </h4>
                <div style="display: flex; gap: 6px; margin-bottom: 8px; flex-wrap: wrap;">
                    <span style="background: {color}22; color: {color}; padding: 2px 8px; 
                           border-radius: 12px; font-size: 11px; font-weight: 600;">
                        Match: {match.similarity_score:.0f}%
                    </span>
                    <span style="background: #818cf822; color: #6366f1; padding: 2px 8px; 
                           border-radius: 12px; font-size: 11px; font-weight: 600;">
                        {ref.sector.value.replace('_', ' ').title()}
                    </span>
                </div>
                <table style="font-size: 12px; color: #374151; width: 100%;">
                    <tr><td>📍</td><td>{ref.location}, {ref.state or 'US'}</td></tr>
                    <tr><td>👥</td><td>{ref.employees} employés</td></tr>
                    <tr><td>💰</td><td>{self._format_revenue(ref.revenue)} CA</td></tr>
                    <tr><td>📈</td><td>{ref.growth_stage.value.replace('_', ' ').title()}</td></tr>
                    {f'<tr><td>🏦</td><td>{self._format_revenue(ref.funding_total)} levés</td></tr>' if ref.funding_total else ''}
                </table>
                <div style="margin-top: 8px; font-size: 11px; color: #6b7280;">
                    {'<br>'.join(f'✓ {r}' for r in match.match_reasons[:3])}
                </div>
            </div>
            """

            folium.Marker(
                location=[ref.latitude, ref.longitude],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{ref.name} — {match.similarity_score:.0f}%",
                icon=folium.Icon(
                    color="green" if tier == "high" else "orange" if tier == "medium" else "red",
                    icon=icon_name,
                    prefix="glyphicon"
                ),
            ).add_to(cluster)

        cluster.add_to(m)

        # Add user's Tunisia location marker
        if user_input:
            user_popup = f"""
            <div style="font-family: 'Inter', Arial, sans-serif; max-width: 250px; padding: 8px;">
                <h4 style="margin: 0 0 8px; color: #1e1b4b;">
                    🇹🇳 Votre Startup
                </h4>
                <table style="font-size: 12px; color: #374151;">
                    <tr><td>📍</td><td>{user_input.location}, Tunisie</td></tr>
                    <tr><td>🏢</td><td>{user_input.sector.value.replace('_', ' ').title()}</td></tr>
                    <tr><td>👥</td><td>{user_input.employees} employés</td></tr>
                    <tr><td>💰</td><td>{user_input.revenue:,.0f} TND</td></tr>
                </table>
            </div>
            """
            folium.Marker(
                location=[user_input.latitude, user_input.longitude],
                popup=folium.Popup(user_popup, max_width=280),
                tooltip=f"🇹🇳 {user_input.company_name or 'Votre Startup'} — {user_input.location}",
                icon=folium.Icon(color="blue", icon="home", prefix="glyphicon"),
            ).add_to(m)

        # Add layer control
        folium.LayerControl().add_to(m)

        # Add a legend
        legend_html = """
        <div style="position: fixed; bottom: 30px; left: 30px; z-index: 1000;
                    background: rgba(30,27,75,0.9); padding: 12px 16px; border-radius: 10px;
                    font-family: 'Inter', Arial, sans-serif; font-size: 12px; color: white;
                    border: 1px solid rgba(129,140,248,0.3);">
            <b style="font-size: 13px;">🗺️ Légende</b><br><br>
            <span style="color: #22c55e;">★</span> Match élevé (≥75%)<br>
            <span style="color: #eab308;">ℹ</span> Match moyen (50-74%)<br>
            <span style="color: #ef4444;">●</span> Match faible (&lt;50%)<br>
            <span style="color: #3b82f6;">🏠</span> Votre startup
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend_html))

        return m
