import * as LucideIcons from 'lucide-vue-next'

/**
 * Resolves a Lucide icon component based on a name or device type.
 * @param {string} name - The icon name, device type, or legacy key.
 * @returns {Component} The Lucide icon component or HelpCircle as fallback.
 */
export function getIcon(name) {
    if (!name) return LucideIcons.HelpCircle

    // 1. Try direct match in Lucide (PascalCase or exactly matching key)
    if (LucideIcons[name]) return LucideIcons[name]

    const normalizedName = name.trim()

    // 2. Auto convert kebab-case to PascalCase
    const pascal = normalizedName.split('-')
        .map(p => p.charAt(0).toUpperCase() + p.slice(1).toLowerCase())
        .join('')
    if (LucideIcons[pascal]) return LucideIcons[pascal]

    // 3. Try lowercase direct match (e.g. 'smartphone' -> 'Smartphone')
    const capitalized = normalizedName.charAt(0).toUpperCase() + normalizedName.slice(1)
    if (LucideIcons[capitalized]) return LucideIcons[capitalized]

    // Fallback
    return LucideIcons.HelpCircle
}
