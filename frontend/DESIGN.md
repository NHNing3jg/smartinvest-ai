# SmartInvest AI Frontend Design System

## 1. Product identity
SmartInvest AI is a Business Intelligence + Artificial Intelligence platform for investment decision support. The final interface should read as a premium Trading Intelligence Cockpit: market-aware, analytical, trustworthy, and competition-ready.

The design is inspired by the Wise getdesign.md system: confident fintech clarity, bold rounded components, strong mint/green accent, high readability, and direct interaction feedback. It is not a Wise clone. SmartInvest adapts that clarity to trading dashboards, BI market intelligence, AI recommendations, backtesting, and portfolio simulation.

## 2. Visual principles
- Trading cockpit, not marketing page.
- Fintech clarity, not decorative noise.
- Deep navy structure, not pure black.
- Mint/green primary accent, inspired by Wise.
- Cyan/blue for BI and data.
- Lavender/purple for AI and model intelligence.
- Amber for HOLD/neutral states.
- Coral/pink/red for SELL, risk, and negative movement.
- Strong contrast on all analytical cards.
- No invented metrics, no fake data, no fake market status.

## 3. Color palette
- Canvas navy: `#071525`, `#0a1d31`, `#102a43`.
- Elevated panel navy: `rgba(13, 32, 52, 0.82)`.
- Strong surface: `rgba(17, 43, 68, 0.9)`.
- Primary Wise-inspired mint: `#9fe870`.
- SmartInvest mint: `#48e99b`.
- Cyan/data: `#10cdbc`, `#38c8ff`.
- BI blue: `#277dff`.
- AI lavender: `#a88bff`.
- HOLD amber: `#ffd86b`.
- SELL/risk coral: `#ff7b7b`, `#ff5da2`.
- Primary text on dark panels: `#f3fbff`.
- Secondary text on dark panels: `#b7c9dc`.
- Muted analytical text: `#8fa6bd`.

Signal mapping:
- BUY = mint/green.
- HOLD = amber/yellow.
- SELL = coral/pink/red.
- BI = cyan/blue.
- AI = mint/lavender.
- Risk = coral or purple depending on context.

## 4. Background rules
- Do not use pure white as the main app background.
- Do not use full black as the main app background.
- Use a deep navy / blue-gray trading canvas with subtle aqua and mint glow.
- Add subtle CSS-only market grid effects where useful.
- Background effects must stay behind the content and never reduce readability.

## 5. Typography rules
- Follow Wise-inspired confidence: heavier headings, clean UI text, direct labels.
- Use dark-on-mint only for primary buttons.
- Use light text on navy cards and panels.
- Keep line-height compact for headings but readable for analytical copy.
- Do not use tiny low-contrast gray for important labels.
- Keep letter spacing at `0` unless an uppercase eyebrow or table heading needs clarity.

## 6. Sidebar rules
- The sidebar should feel like a professional trading platform module rail.
- Use navy/blue-tinted glass with thin mint/cyan highlights.
- Keep the official SmartInvest logo visible and clear.
- Active navigation must be obvious: mint accent, stronger border, glow, and readable label.
- Preserve all existing routes.
- Do not add "Competition Mode".
- Do not add the old "BI + AI / Student fintech studio" card.

## 7. Header rules
- The header should read like a market dashboard top bar.
- Keep search and notification controls.
- Use navy glass, compact spacing, and mint/cyan accents.
- Static product labels are allowed; fake metrics or fake live market values are not.
- Align with the main content and avoid excessive empty space.

## 8. Hero section rules
- Heroes should look like cockpit command panels, not soft pastel banners.
- Use deep navy gradients with mint/cyan/lavender glows.
- Keep hero copy readable with light text.
- Hero visual motifs may be abstract bars, rings, strips, or module blocks, but must stay subtle.

## 9. KPI card rules
- KPI cards should feel like trading metric tiles.
- Use dark glass surfaces, thin borders, and small accent glows.
- Values must be prominent and readable.
- Icons should sit in compact square mint/cyan/blue/lavender capsules.
- Do not add new metrics or change API-derived values.

## 10. Chart card rules
- Chart panels should feel like market dashboard chart wells.
- Use darker chart surfaces with subtle grid backgrounds.
- Keep Recharts readable: axes, legends, tooltips, and labels must be visible.
- Use stable chart heights.
- Empty chart states must show clear copy, not blank containers.
- Do not remove Recharts or change the data source.

## 11. Table rules
- Tables should look like professional market data tables.
- Use dark rows, high-contrast headers, and readable cell spacing.
- Keep limited rows by default and preserve Show more / Show less behavior.
- Horizontal scroll is acceptable for wide analytical tables.
- Do not remove useful columns.

## 12. Filter panel rules
- Filters should look like trading dashboard controls.
- Inputs and selects use dark navy fields with light text.
- Buttons align with controls and wrap cleanly.
- Keep endpoint parameters and request behavior unchanged.

## 13. Buttons and interaction
- Primary buttons use Wise-inspired mint/green with dark green text.
- Buttons should have pill shape and subtle scale hover/active behavior.
- Secondary buttons use dark navy glass with mint/cyan border.
- Focus states must be visible.

## 14. Loading, error, and empty states
- Loading states live inside dark glass panels.
- Error states use coral accents but stay calm and readable.
- Empty states explain missing API data without inventing replacements.
- Never add mock values to make a state look populated.

## 15. Responsive rules
- No horizontal overflow at the app shell level.
- Sidebar converts to compact top navigation on tablet/mobile.
- KPI grids collapse to two columns, then one column.
- Chart heights remain stable and legends stay visible.
- Mobile table cards remain readable.

## 16. Accessibility rules
- Maintain strong text contrast on dark navy cards.
- Do not rely on color alone; BUY/HOLD/SELL text labels remain visible.
- Hit targets should be at least 44px high where practical.
- Focus states need visible mint outlines.
- Avoid chart labels that collide or overflow.

## 17. Do / Don't examples
Do:
- Use a deep navy trading canvas with mint and aqua glow.
- Use Wise-inspired mint for primary actions and BUY semantics.
- Use glass panels with strong contrast and thin borders.
- Keep charts, tables, and cards data-driven.
- Preserve SmartInvest AI's BI + AI personality.

Don't:
- Do not use a plain white app canvas.
- Do not use a full black crypto theme.
- Do not create a Binance clone.
- Do not create a childish, gaming, or meme-crypto style.
- Do not invent data, metrics, endpoints, or market values.
- Do not remove pages, charts, or useful tables.

## 18. Future AI coding-agent instructions
- Work inside `frontend/` for UI/design tasks unless explicitly instructed otherwise.
- Do not modify backend, Streamlit, ML, or outputs for visual-only work.
- Keep existing API loading and endpoint contracts intact.
- Prefer controlled CSS/component polish over a rewrite.
- Use the Wise getdesign.md system as inspiration for clarity, green accent, rounded components, and confident interaction.
- Adapt the final result to SmartInvest AI as a professional trading intelligence cockpit.
- Run `npm run build` from `frontend/` before reporting completion.
