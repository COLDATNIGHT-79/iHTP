/**
 * Image URL handler for multiple platforms
 * Transforms social media URLs to embeddable image URLs
 */

const ImageEmbed = {
    // Platform detection patterns
    patterns: {
        // Imgur - transform to direct image
        imgur: {
            match: /imgur\.com\/(?:a\/)?(\w+)/i,
            transform: (id) => `https://i.imgur.com/${id}.jpg`
        },
        // Imgur direct (already good)
        imgurDirect: {
            match: /i\.imgur\.com\/(\w+)\.(jpg|png|gif|webp)/i,
            transform: null // No transform needed
        },
        // Discord CDN
        discord: {
            match: /cdn\.discordapp\.com\/.+/i,
            transform: null // Already direct
        },
        // Discord Media
        discordMedia: {
            match: /media\.discordapp\.net\/.+/i,
            transform: null // Already direct
        },
        // Twitter/X images
        twitter: {
            match: /pbs\.twimg\.com\/media\/(\w+)/i,
            transform: null // Already direct
        },
        // Instagram (limited - needs proxy in production)
        instagram: {
            match: /instagram\.com\/p\/(\w+)/i,
            transform: null // Can't direct link easily
        },
        // Giphy
        giphy: {
            match: /giphy\.com\/gifs\/(?:.*-)?(\w+)/i,
            transform: (id) => `https://media.giphy.com/media/${id}/giphy.gif`
        },
        // Reddit preview images
        reddit: {
            match: /preview\.redd\.it\/(\w+\.\w+)/i,
            transform: null
        },
        // Standard image extensions
        directImage: {
            match: /\.(jpg|jpeg|png|gif|webp|bmp|svg)(\?.*)?$/i,
            transform: null
        }
    },

    /**
     * Process a URL and return the best embeddable version
     */
    processUrl: function (url) {
        if (!url) return null;

        url = url.trim();

        // Try each pattern
        for (const [platform, config] of Object.entries(this.patterns)) {
            const match = url.match(config.match);
            if (match) {
                if (config.transform) {
                    return config.transform(match[1]);
                }
                return url;
            }
        }

        // If no pattern matched but looks like an image URL, try it anyway
        return url;
    },

    /**
     * Create an image element with fallback handling
     */
    createImage: function (url, alt = 'Image') {
        const processedUrl = this.processUrl(url);

        const img = document.createElement('img');
        img.src = processedUrl;
        img.alt = alt;
        img.crossOrigin = 'anonymous';

        img.onerror = function () {
            this.onerror = null;
            this.parentElement.innerHTML = '<span class="image-error">[Image unavailable]</span>';
        };

        return img;
    },

    /**
     * Update preview box with image
     */
    updatePreview: function (url, containerId = 'image-preview') {
        const container = document.getElementById(containerId);
        if (!container) return;

        if (!url || !url.trim()) {
            container.innerHTML = '<span class="preview-placeholder">image preview</span>';
            return;
        }

        const processedUrl = this.processUrl(url);
        container.innerHTML = `<img src="${processedUrl}" alt="Preview" onerror="this.onerror=null; this.outerHTML='<span class=\\'preview-placeholder\\'>[Invalid or inaccessible URL]</span>'">`;
    }
};

// Expose globally
window.ImageEmbed = ImageEmbed;

// Helper function for inline use
function updatePreview(url) {
    ImageEmbed.updatePreview(url);
}
