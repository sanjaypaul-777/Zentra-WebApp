"""Canonical Help Center seed content for BrandBox.

Articles reference real dashboard labels and flows. Features that are stubs
use is_coming_soon=True with a short Coming soon body instead of invented detail.
"""

from __future__ import annotations

# Each category: slug, name, description, icon, sort_order, articles[]
# Each article: slug, title, summary, body (HTML), is_coming_soon, sort_order

CATEGORIES = [
    {
        "slug": "getting-started",
        "name": "Getting Started",
        "description": "Create your account, finish onboarding, and connect Shopify.",
        "icon": "rocket_launch",
        "sort_order": 1,
        "articles": [
            {
                "slug": "what-is-brandbox",
                "title": "What is BrandBox?",
                "summary": "AI store builder, Product Hunter, imports, and coach support.",
                "body": """
<p>BrandBox helps you launch and grow a Shopify store with less busywork.</p>
<p>Inside your dashboard you get:</p>
<ol>
<li><strong>AI Store Builder</strong> — pick a niche, confirm, and build a themed store with products.</li>
<li><strong>Product Hunter / AI Picks</strong> — browse scored products in the vault.</li>
<li><strong>My Imports</strong> — stage products, then push them to Shopify.</li>
<li><strong>My Stores</strong> — manage connected shops.</li>
<li><strong>BrandBox Coach</strong> — chat for guidance when you get stuck.</li>
</ol>
<p>BrandBox does not create ads or handle shipping for you — those stay with you and Shopify.</p>
""",
            },
            {
                "slug": "creating-your-account",
                "title": "Creating your BrandBox account",
                "summary": "Sign up from the homepage or checkout.",
                "body": """
<p>You can create an account in two ways:</p>
<ol>
<li>From the homepage, click <strong>Sign Up</strong> / create account, then complete the form.</li>
<li>From <strong>Checkout</strong>, create an account as part of claiming a plan offer.</li>
</ol>
<p>After signup you’ll usually continue into onboarding, then land in the dashboard at <code>/dashboard/</code>.</p>
""",
            },
            {
                "slug": "completing-onboarding",
                "title": "Completing the onboarding questionnaire",
                "summary": "Tell BrandBox about your goals before you enter the dashboard.",
                "body": """
<p>Onboarding asks a short set of profile questions (goals, time, challenges, and related preferences).</p>
<ol>
<li>Open <code>/onboarding/</code> if you’re redirected there after login.</li>
<li>Fill each step and continue until finished.</li>
<li>You’ll be taken to the dashboard Overview when onboarding is complete.</li>
</ol>
<p>You can update many profile details later under <strong>Settings</strong>.</p>
""",
            },
            {
                "slug": "connecting-existing-shopify",
                "title": "Connecting an existing Shopify store",
                "summary": "Use Connect Shopify from Overview or My Stores.",
                "body": """
<p>If you already have a Shopify store:</p>
<ol>
<li>On Overview (when not connected), choose <strong>Connect</strong> on the Connect Shopify card — or open <strong>My Stores</strong> and use <strong>+ Connect another store</strong>.</li>
<li>Enter your <code>*.myshopify.com</code> domain on the connect flow.</li>
<li>Install the BrandBox app when Shopify prompts you.</li>
<li>Return to BrandBox — Overview switches to the connected dashboard once the app is installed.</li>
</ol>
""",
            },
            {
                "slug": "creating-new-shopify-store",
                "title": "Creating a new Shopify store (if you don't have one)",
                "summary": "Use Create Shopify Account, then come back to connect.",
                "body": """
<p>If you don’t have Shopify yet:</p>
<ol>
<li>On Overview, open the <strong>Create Shopify Account</strong> card and click <strong>Create account</strong>.</li>
<li>Finish Shopify’s signup in a new flow.</li>
<li>Return to BrandBox and use <strong>Connect</strong> with your new <code>*.myshopify.com</code> domain.</li>
<li>Install the BrandBox app, then continue in the dashboard.</li>
</ol>
""",
            },
            {
                "slug": "installing-brandbox-app",
                "title": "Installing the BrandBox app on your store",
                "summary": "App install is required before builds and product pushes.",
                "body": """
<p>BrandBox needs the app installed on your Shopify store to build and sync products.</p>
<ol>
<li>Start from <strong>Connect</strong> and submit your shop domain.</li>
<li>Approve the BrandBox app install in Shopify when prompted.</li>
<li>When install completes, BrandBox marks the shop as connected (app installed).</li>
</ol>
<p>If Overview still shows the connect screen, confirm the install finished and refresh, or reconnect from <strong>My Stores</strong> / Settings.</p>
""",
            },
            {
                "slug": "setting-password-after-checkout",
                "title": "Setting your password (if you signed up via checkout)",
                "summary": "Use password change / forgot password if you need to set credentials.",
                "body": """
<p>If you created your account during checkout:</p>
<ol>
<li>Use the login email from checkout to sign in at <code>/login/</code>.</li>
<li>If you don’t have a password yet, use <strong>Forgot password</strong> or <strong>Change password</strong> from account settings once logged in.</li>
<li>Set a password you can remember, then return to the dashboard.</li>
</ol>
""",
            },
            {
                "slug": "understanding-dashboard-first-time",
                "title": "Understanding your dashboard for the first time",
                "summary": "Overview, builder, hunter, imports, stores, coach, and settings.",
                "body": """
<p>The left sidebar is your main map:</p>
<ol>
<li><strong>Overview</strong> — readiness, activity, and next-step CTAs like <strong>Create AI Store</strong> or <strong>Build Another Store</strong>.</li>
<li><strong>AI Store Builder</strong> — niche pick → confirm → build.</li>
<li><strong>Product Hunter</strong> / <strong>AI Picks</strong> — find products.</li>
<li><strong>My Imports</strong> — review and push products.</li>
<li><strong>My Stores</strong> — connected shops.</li>
<li><strong>Schedule</strong>, <strong>BrandBox Coach</strong>, <strong>Training</strong>, <strong>Settings</strong>.</li>
</ol>
<p>If you’re not connected yet, Overview shows Connect / Create Shopify cards first.</p>
""",
            },
        ],
    },
    {
        "slug": "ai-store-builder",
        "name": "AI Store Builder",
        "description": "Niche selection, confirmation, and build status.",
        "icon": "auto_awesome",
        "sort_order": 2,
        "articles": [
            {
                "slug": "how-ai-store-builder-works",
                "title": "How the AI Store Builder works",
                "summary": "Two steps: choose niche, then confirm and launch the build.",
                "body": """
<p>AI Store Builder is a short wizard:</p>
<ol>
<li><strong>Step 1 — Choose your niche</strong> — pick one niche card, then click <strong>Next</strong>.</li>
<li><strong>Step 2 — Ready to build your store</strong> — review the summary and start the build.</li>
</ol>
<p>The build runs against your connected Shopify store. When it finishes you’ll see success status screens under the builder flow.</p>
""",
            },
            {
                "slug": "choosing-a-niche",
                "title": "Choosing a niche",
                "summary": "Select a niche card, then click Next.",
                "body": """
<ol>
<li>Open <strong>AI Store Builder</strong>.</li>
<li>Browse the niche grid (codename + category under each theme preview).</li>
<li>Click a niche to select it (selected card highlights).</li>
<li>Click <strong>Next</strong> to continue. The button stays disabled until a niche is selected.</li>
</ol>
<p>You can change niches later by starting another build — changing niche resets the product seed for that session.</p>
""",
            },
            {
                "slug": "whats-included-in-each-niche",
                "title": "What's included in each niche (theme + products)?",
                "summary": "Each niche maps to a BrandBox theme and a product pack count.",
                "body": """
<p>Each niche pack includes:</p>
<ol>
<li>A matching theme name (for example BrandBox Living, BrandBox Peak).</li>
<li>A product set for that niche (counts sync from BrandBox’s niche engine when available).</li>
<li>POD (Print on Demand) is special — it can have zero engine products.</li>
</ol>
<p>Card previews on Step 1 show the theme mockup for that niche.</p>
""",
            },
            {
                "slug": "ai-picked-vs-own-products",
                "title": "Using AI-picked winning products vs. adding your own",
                "summary": "Builder seeds niche products; Product Hunter adds more later.",
                "body": """
<p>During a default build, BrandBox uses the niche’s AI/product pack as the starting catalog.</p>
<p>After the store exists, use <strong>Product Hunter</strong> or <strong>AI Picks</strong> to import more winning products into <strong>My Imports</strong>, then push them live.</p>
<p>Editing your own custom catalog details is done from imports / Shopify after push — the builder itself focuses on niche + theme setup.</p>
""",
            },
            {
                "slug": "build-confirmation-screen",
                "title": "Understanding the build confirmation screen",
                "summary": "Step 2 shows niche, theme, and product summary before you launch.",
                "body": """
<p>On Step 2 (<strong>Ready to build your store</strong>) you’ll see a summary of:</p>
<ol>
<li>Selected niche</li>
<li>Theme</li>
<li>Product count / mode for this build</li>
</ol>
<p>Copy on this screen reminds you the build happens inside your own Shopify store. Confirm only when the summary looks right.</p>
""",
            },
            {
                "slug": "what-happens-during-build",
                "title": "What happens during the build process?",
                "summary": "Builder job screens: start → building → success.",
                "body": """
<ol>
<li>After confirmation, BrandBox starts a build job for your shop.</li>
<li>You’ll see building/progress status pages while work runs.</li>
<li>On success, you’re guided back toward the dashboard / store.</li>
</ol>
<p>Keep the shop connected and the BrandBox app installed while the job runs.</p>
""",
            },
            {
                "slug": "what-to-do-if-build-fails",
                "title": "What to do if a build fails?",
                "summary": "Reconnect the app, retry from My Stores or Builder.",
                "body": """
<ol>
<li>Confirm the BrandBox app is still installed on Shopify.</li>
<li>Open <strong>My Stores</strong> and check store status / retry actions if shown.</li>
<li>Return to <strong>AI Store Builder</strong> and run the flow again if needed.</li>
<li>If Live Products or readiness looks wrong on Overview, reconnect under Settings / My Stores.</li>
</ol>
""",
            },
            {
                "slug": "editing-store-after-built",
                "title": "Editing your store after it's built",
                "summary": "Use Shopify admin plus BrandBox imports for catalog updates.",
                "body": """
<p>After a successful build:</p>
<ol>
<li>Open your live storefront from Overview (<strong>View Live Store</strong>) when available.</li>
<li>Edit theme/content in Shopify admin as usual.</li>
<li>Add more products via Product Hunter → My Imports → push.</li>
</ol>
<p>BrandBox readiness on Overview tracks setup checklist items as you finish them.</p>
""",
            },
            {
                "slug": "building-more-than-one-store",
                "title": "Building more than one store",
                "summary": "Use Build Another Store or connect another shop first.",
                "body": """
<ol>
<li>On Overview (when you already have a build), click <strong>Build Another Store</strong>.</li>
<li>Or connect an additional shop from <strong>My Stores</strong> with <strong>+ Connect another store</strong>, then run Builder for that shop.</li>
<li>Complete niche → confirm → build again.</li>
</ol>
""",
            },
        ],
    },
    {
        "slug": "winning-product-hunter",
        "name": "Winning Product Hunter",
        "description": "Scores, trends, imports, and publishing.",
        "icon": "travel_explore",
        "sort_order": 3,
        "articles": [
            {
                "slug": "how-product-hunter-finds-products",
                "title": "How Product Hunter finds products",
                "summary": "Search and filter the Winning Product Vault.",
                "body": """
<ol>
<li>Open <strong>Product Hunter</strong> (or <strong>AI Picks</strong> for curated picks).</li>
<li>Use <strong>Search</strong> plus filters like country / niche when available.</li>
<li>Browse cards in the vault. If empty, products need to be synced/loaded by your BrandBox admin.</li>
</ol>
<p>You need a connected Shopify store before import buttons unlock.</p>
""",
            },
            {
                "slug": "understanding-winning-score",
                "title": "Understanding the Winning Score",
                "summary": "Higher scores highlight stronger vault candidates.",
                "body": """
<p>Each vault product can show a Winning Score used to rank opportunity.</p>
<p>Use it as a relative signal alongside trend, margin, and shipping estimates on the product card — not as a guarantee of sales.</p>
""",
            },
            {
                "slug": "reading-trend-data",
                "title": "Reading trend data",
                "summary": "Trend fields on product cards show demand direction.",
                "body": """
<p>Where trend data is present on a Product Hunter card, treat it as supporting context for demand direction.</p>
<p>Combine it with Winning Score and margin estimates before you click import.</p>
""",
            },
            {
                "slug": "profit-margin-estimates",
                "title": "Understanding profit margin estimates",
                "summary": "Margin and profit calculator fields are estimates.",
                "body": """
<p>Product cards may show estimated profit / margin and a simple profit calculator.</p>
<p>These are planning estimates — your real costs (ads, shipping, fees) can differ. Adjust assumptions before you push live.</p>
""",
            },
            {
                "slug": "shipping-cost-delivery-estimates",
                "title": "Understanding shipping cost/delivery time estimates",
                "summary": "Shipping fields are estimates from vault data.",
                "body": """
<p>When shipping cost or delivery estimates appear on a product, use them to sanity-check logistics before import.</p>
<p>Final shipping rules are configured in Shopify / your supplier — BrandBox does not fulfill orders.</p>
""",
            },
            {
                "slug": "competitor-research-data",
                "title": "Understanding competitor research data",
                "summary": "Competitor signals help compare positioning.",
                "body": """
<p>Some vault products include competitor research snippets.</p>
<p>Use them to compare pricing and positioning — they don’t replace your own store research.</p>
""",
            },
            {
                "slug": "importing-product-to-store",
                "title": "Importing a product to your store",
                "summary": "Import stages a product into My Imports — it is not live yet.",
                "body": """
<ol>
<li>Connect Shopify if you haven’t (import requires <code>can_import</code>).</li>
<li>On a product card, click the import button.</li>
<li>If already imported, you’ll see an imported badge linking to <strong>My Imports</strong>.</li>
<li>Open <strong>My Imports</strong> to review, then push to Shopify.</li>
</ol>
""",
            },
            {
                "slug": "editing-imported-before-publishing",
                "title": "Editing an imported product before publishing",
                "summary": "Edit from My Imports before you push live.",
                "body": """
<ol>
<li>Go to <strong>My Imports</strong>.</li>
<li>Open the product you imported.</li>
<li>Update details shown in the imports editor.</li>
<li>Push when ready — edits after push may also require Shopify admin changes.</li>
</ol>
""",
            },
        ],
    },
    {
        "slug": "my-imports",
        "name": "My Imports",
        "description": "Stage, edit, and push products to Shopify.",
        "icon": "inventory_2",
        "sort_order": 4,
        "articles": [
            {
                "slug": "what-is-my-imports",
                "title": "What is My Imports?",
                "summary": "Your staging area between the vault and Shopify.",
                "body": """
<p><strong>My Imports</strong> holds products you’ve imported from Product Hunter / AI Picks before they go live.</p>
<p>Use it to review details, remove items you don’t want, and push one or many products to your connected store.</p>
""",
            },
            {
                "slug": "editing-product-details-before-push",
                "title": "Editing product details before pushing live",
                "summary": "Fix titles and details in imports first.",
                "body": """
<ol>
<li>Open <strong>My Imports</strong>.</li>
<li>Select a product and edit available fields.</li>
<li>Save your changes.</li>
<li>Push to Shopify when the listing looks right.</li>
</ol>
""",
            },
            {
                "slug": "removing-product-from-imports",
                "title": "Removing a product from your imports",
                "summary": "Remove staged items you don’t plan to push.",
                "body": """
<ol>
<li>Open <strong>My Imports</strong>.</li>
<li>Find the product.</li>
<li>Use the remove / delete action on that row.</li>
<li>Confirm if prompted — this removes it from staging, not from Shopify (unless it was already pushed).</li>
</ol>
""",
            },
            {
                "slug": "pushing-single-product",
                "title": "Pushing a single product to your store",
                "summary": "Push one import at a time to Shopify.",
                "body": """
<ol>
<li>Open <strong>My Imports</strong>.</li>
<li>Choose one product.</li>
<li>Click the push / publish action for that item.</li>
<li>Wait for success — then verify in Shopify admin.</li>
</ol>
""",
            },
            {
                "slug": "pushing-multiple-products",
                "title": "Pushing multiple products at once",
                "summary": "Select several imports and push together when available.",
                "body": """
<ol>
<li>In <strong>My Imports</strong>, select multiple products if bulk actions are shown.</li>
<li>Choose the bulk push action.</li>
<li>Review any failures individually and retry.</li>
</ol>
""",
            },
            {
                "slug": "what-if-push-fails",
                "title": "What happens if a push fails?",
                "summary": "Check connection, retry the import push.",
                "body": """
<ol>
<li>Confirm the BrandBox app is installed and the store is still connected.</li>
<li>Open the failed item in My Imports and retry push.</li>
<li>If it keeps failing, reconnect the store from My Stores / Settings, then try again.</li>
</ol>
""",
            },
        ],
    },
    {
        "slug": "my-stores",
        "name": "My Stores",
        "description": "Connected shops, status, and disconnect.",
        "icon": "storefront",
        "sort_order": 5,
        "articles": [
            {
                "slug": "viewing-connected-stores",
                "title": "Viewing all your connected stores",
                "summary": "Open My Stores for the full shop list.",
                "body": """
<ol>
<li>Click <strong>My Stores</strong> in the sidebar.</li>
<li>Review each row’s shop domain, status, and primary action.</li>
<li>If none are connected, use <strong>Connect your first store</strong>.</li>
</ol>
""",
            },
            {
                "slug": "understanding-store-status",
                "title": "Understanding store status",
                "summary": "Status shows connection / build health per shop.",
                "body": """
<p>Each store row shows status for that connection (connected, needs attention, etc.).</p>
<p>Use the primary button on the row (continue build, open store, retry) based on what’s offered for that status.</p>
""",
            },
            {
                "slug": "connecting-additional-store",
                "title": "Connecting an additional store",
                "summary": "Use + Connect another store.",
                "body": """
<ol>
<li>Open <strong>My Stores</strong>.</li>
<li>Click <strong>+ Connect another store</strong>.</li>
<li>Enter the new <code>*.myshopify.com</code> domain and install the app.</li>
<li>The new shop appears in the list when connected.</li>
</ol>
""",
            },
            {
                "slug": "retrying-failed-build",
                "title": "Retrying a failed build",
                "summary": "Use store row actions or AI Store Builder again.",
                "body": """
<ol>
<li>In <strong>My Stores</strong>, open the shop with the failed build.</li>
<li>Use retry / continue if shown on the row.</li>
<li>Or reopen <strong>AI Store Builder</strong>, select niche, and confirm again.</li>
</ol>
""",
            },
            {
                "slug": "disconnecting-a-store",
                "title": "Disconnecting a store",
                "summary": "Disconnect from My Stores after confirming.",
                "body": """
<ol>
<li>Open <strong>My Stores</strong>.</li>
<li>Choose disconnect for that shop.</li>
<li>Confirm with <strong>Disconnect store</strong> in the confirmation dialog.</li>
</ol>
<p>You can reconnect later with Connect if needed.</p>
""",
            },
        ],
    },
    {
        "slug": "billing-plans",
        "name": "Billing & Plans",
        "description": "Free vs Pro and upgrade paths.",
        "icon": "payments",
        "sort_order": 6,
        "articles": [
            {
                "slug": "free-vs-pro",
                "title": "Free vs. Pro",
                "summary": "Plan label appears in the dashboard; Pro unlocks upgrade features list.",
                "body": """
<p>Your account has a plan flag (Free or Pro) shown in the dashboard shell.</p>
<p>Open <strong>Upgrade</strong> to see current plan options. Live coach eligibility is controlled by product settings and may change — check Upgrade or ask in Coach chat for what’s available on your account.</p>
""",
            },
            {
                "slug": "how-billing-works",
                "title": "How billing works",
                "summary": "Checkout collects account intent; full payment provider wiring may still be rolling out.",
                "body": """
<p>Plan changes are managed through Checkout / Upgrade flows and admin plan flags.</p>
<p><em>Note:</em> Automated payment-provider charging may still be expanding — if checkout succeeds but Pro isn’t active, contact support or check Upgrade status.</p>
""",
                "is_coming_soon": True,
            },
            {
                "slug": "upgrading-to-pro",
                "title": "Upgrading to Pro",
                "summary": "Use the Upgrade page from the dashboard.",
                "body": """
<ol>
<li>Open <strong>Upgrade</strong> from the dashboard.</li>
<li>Review Pro features.</li>
<li>Continue through checkout / upgrade CTA when offered.</li>
</ol>
""",
            },
            {
                "slug": "cancelling-or-downgrading",
                "title": "Cancelling or downgrading",
                "summary": "Coming soon — self-serve cancel may not be fully wired yet.",
                "body": """
<p><strong>Coming soon.</strong> Self-serve cancel/downgrade isn’t fully documented in-app yet.</p>
<p>Contact support from Contact Us or Coach Chat if you need plan help.</p>
""",
                "is_coming_soon": True,
            },
            {
                "slug": "payment-fails",
                "title": "What happens if my payment fails?",
                "summary": "Coming soon — retry checkout or contact support.",
                "body": """
<p><strong>Coming soon.</strong> Detailed payment-failure recovery depends on the payment provider integration.</p>
<p>Retry checkout, or reach out via Contact Us / Coach Chat.</p>
""",
                "is_coming_soon": True,
            },
            {
                "slug": "requesting-a-refund",
                "title": "Requesting a refund",
                "summary": "See Refund Policy; contact support to request.",
                "body": """
<p>Read the public <a href="/refund/">Refund Policy</a> for eligibility.</p>
<p>To request a refund, contact support via Contact Us with your account email and order details.</p>
""",
            },
        ],
    },
    {
        "slug": "account-settings",
        "name": "Account & Settings",
        "description": "Profile, password, notifications, defaults.",
        "icon": "settings",
        "sort_order": 7,
        "articles": [
            {
                "slug": "updating-account-information",
                "title": "Updating your account information",
                "summary": "Edit profile fields under Settings.",
                "body": """
<ol>
<li>Open <strong>Settings</strong> in the sidebar.</li>
<li>Go to profile / account fields.</li>
<li>Update your information and save.</li>
</ol>
""",
            },
            {
                "slug": "changing-your-password",
                "title": "Changing your password",
                "summary": "Use password change from account settings or /password/change/.",
                "body": """
<ol>
<li>While logged in, open the password change page / Settings password option.</li>
<li>Enter your current and new password.</li>
<li>Save, then sign in again if prompted.</li>
</ol>
""",
            },
            {
                "slug": "managing-notification-preferences",
                "title": "Managing notification preferences",
                "summary": "Toggle notifications in Settings.",
                "body": """
<ol>
<li>Open <strong>Settings</strong>.</li>
<li>Find notification preferences.</li>
<li>Toggle options and save.</li>
</ol>
""",
            },
            {
                "slug": "setting-default-niche",
                "title": "Setting default niche/preferences",
                "summary": "Default niche pre-selects AI Store Builder.",
                "body": """
<ol>
<li>Open <strong>Settings</strong>.</li>
<li>Set your default niche preference when available.</li>
<li>AI Store Builder can pre-select that niche on your next visit.</li>
</ol>
""",
            },
            {
                "slug": "deleting-your-account",
                "title": "Deleting your account",
                "summary": "Request deletion via support / GDPR article.",
                "body": """
<p>Account deletion is handled as a data request.</p>
<p>See <strong>Data deletion requests (GDPR)</strong> under Policies, or contact support with the email on your account.</p>
""",
            },
        ],
    },
    {
        "slug": "academy",
        "name": "Academy",
        "description": "Training lessons (rolling out).",
        "icon": "school",
        "sort_order": 8,
        "articles": [
            {
                "slug": "how-academy-works",
                "title": "How Academy works",
                "summary": "Training page is a stub today.",
                "body": """
<p><strong>Coming soon.</strong> The dashboard <strong>Training</strong> page currently shows a placeholder for on-demand lessons (builder, picks, imports).</p>
<p>Full Academy lessons and progress tracking aren’t shipped yet.</p>
""",
                "is_coming_soon": True,
            },
            {
                "slug": "tracking-lesson-progress",
                "title": "Tracking your lesson progress",
                "summary": "Coming soon.",
                "body": """
<p><strong>Coming soon.</strong> Lesson progress tracking will appear here when Academy content launches.</p>
""",
                "is_coming_soon": True,
            },
            {
                "slug": "recommended-lessons-beginners",
                "title": "Recommended lessons for beginners",
                "summary": "Coming soon — start with Getting Started articles meanwhile.",
                "body": """
<p><strong>Coming soon.</strong> Until Academy lessons launch, use Getting Started and AI Store Builder articles in this Help Center.</p>
""",
                "is_coming_soon": True,
            },
        ],
    },
    {
        "slug": "coach-chat-support",
        "name": "Coach Chat / Support",
        "description": "AI answers, coaches, and when to escalate.",
        "icon": "support_agent",
        "sort_order": 9,
        "articles": [
            {
                "slug": "how-coach-chat-works",
                "title": "How Coach Chat works",
                "summary": "Open BrandBox Coach for chat plus Help Center suggestions.",
                "body": """
<ol>
<li>Open <strong>BrandBox Coach</strong> in the sidebar.</li>
<li>Ask a question in the chat box.</li>
<li>BrandBox AI replies using Help Center matches when possible, and may link articles for you to read.</li>
<li>If you still need a person, use <strong>Still need help? Chat with us</strong> / transfer (sign-in required; live coach availability depends on your plan).</li>
</ol>
""",
            },
            {
                "slug": "ai-vs-real-coach",
                "title": "When you'll talk to AI vs. a real coach",
                "summary": "AI answers first; coaches when available after transfer.",
                "body": """
<p>By default, chat uses BrandBox AI plus Help Center articles so you get instant guidance.</p>
<p>A real coach joins when you request transfer and a coach is available — and your account is eligible under the current plan rules (these can change; ask Coach Agent or check Upgrade).</p>
""",
            },
            {
                "slug": "getting-help-when-stuck",
                "title": "Getting help when you're stuck",
                "summary": "Search Help, ask Coach, or Contact Us.",
                "body": """
<ol>
<li>Search this Help Center for your topic.</li>
<li>Ask BrandBox Coach — it can point you to articles.</li>
<li>If that’s not enough, request a live coach transfer if available on your account, or use <strong>Contact Us</strong>.</li>
</ol>
""",
            },
        ],
    },
    {
        "slug": "affiliate-program",
        "name": "Affiliate Program",
        "description": "Apply and grow with BrandBox affiliates.",
        "icon": "handshake",
        "sort_order": 10,
        "articles": [
            {
                "slug": "how-to-apply",
                "title": "How to apply",
                "summary": "Use the public Affiliate page and register form.",
                "body": """
<ol>
<li>Open the <a href="/affiliate/">Affiliate</a> landing page.</li>
<li>Click through to <strong>register</strong> / apply.</li>
<li>Submit the application form.</li>
<li>Wait for review — status is managed in BrandBox admin (pending → reviewing → approved/rejected).</li>
</ol>
""",
            },
            {
                "slug": "application-review-timeline",
                "title": "Application review timeline",
                "summary": "Applications are reviewed manually in admin.",
                "body": """
<p>Applications move through pending / reviewing / approved / rejected in admin.</p>
<p>Timing varies — watch your email for updates after you apply.</p>
""",
            },
            {
                "slug": "commission-structure",
                "title": "Commission structure",
                "summary": "See the Affiliate landing page for current offer details.",
                "body": """
<p>Commission details are published on the public Affiliate page marketing content.</p>
<p>Approved partners receive program specifics after approval.</p>
""",
            },
            {
                "slug": "how-payouts-work",
                "title": "How payouts work",
                "summary": "Partner payout portal is still rolling out.",
                "body": """
<p><strong>Coming soon.</strong> A full partner dashboard for payouts isn’t fully built yet. Approved partners are guided after approval (login path referenced on the affiliate pages).</p>
""",
                "is_coming_soon": True,
            },
            {
                "slug": "tracking-your-referrals",
                "title": "Tracking your referrals",
                "summary": "Coming soon in the partner experience.",
                "body": """
<p><strong>Coming soon.</strong> Referral tracking UI for affiliates will expand with the partner dashboard.</p>
""",
                "is_coming_soon": True,
            },
            {
                "slug": "application-not-approved",
                "title": "What happens if my application isn't approved?",
                "summary": "Rejected applications can reapply or contact support.",
                "body": """
<p>If your application is rejected, you’ll be notified based on the review process.</p>
<p>You can update your materials and apply again later, or contact support with questions.</p>
""",
            },
        ],
    },
    {
        "slug": "shopify-specific",
        "name": "Shopify-Specific",
        "description": "Permissions, existing stores, uninstall impact.",
        "icon": "shopping_bag",
        "sort_order": 11,
        "articles": [
            {
                "slug": "what-permissions-needed",
                "title": "What permissions does BrandBox need on my store?",
                "summary": "Permissions are requested during app install.",
                "body": """
<p>When you install BrandBox, Shopify shows the permission scopes the app needs to build themes/products and sync catalog changes.</p>
<p>Approve only if you’re comfortable — without install, builds and pushes won’t work.</p>
""",
            },
            {
                "slug": "use-with-existing-selling-store",
                "title": "Can I use BrandBox with a store I already sell on?",
                "summary": "Yes — connect the existing shop, then be careful with live catalogs.",
                "body": """
<p>Yes. Connect your existing <code>*.myshopify.com</code> store and install the app.</p>
<p>Builds and product pushes write into that store — review imports carefully if you already have live products and theme customizations.</p>
""",
            },
            {
                "slug": "what-if-i-uninstall-app",
                "title": "What happens if I uninstall the app?",
                "summary": "BrandBox loses API access until you reinstall.",
                "body": """
<p>If you uninstall BrandBox from Shopify, builds/pushes stop working until you reconnect and reinstall.</p>
<p>Products already in Shopify generally remain — BrandBox simply can’t manage them until the app is back.</p>
""",
            },
            {
                "slug": "affect-existing-theme-products",
                "title": "Does BrandBox affect my existing theme/products?",
                "summary": "Builds can add theme/catalog content — review before running on a live shop.",
                "body": """
<p>AI Store Builder applies niche theme/product setup into your connected store.</p>
<p>On a store you already sell from, treat builds and bulk pushes as production changes — preview and push deliberately.</p>
""",
            },
        ],
    },
    {
        "slug": "troubleshooting",
        "name": "Troubleshooting",
        "description": "Fix connect, build, login, and payment issues.",
        "icon": "build",
        "sort_order": 12,
        "articles": [
            {
                "slug": "store-wont-connect",
                "title": "Store won't connect?",
                "summary": "Check domain format, install, and retry Connect.",
                "body": """
<ol>
<li>Use the full <code>your-store.myshopify.com</code> domain.</li>
<li>Complete the Shopify app install prompt.</li>
<li>Return to BrandBox and refresh Overview / My Stores.</li>
<li>Try <strong>Connect</strong> again from Overview or My Stores.</li>
</ol>
""",
            },
            {
                "slug": "build-stuck-or-slow",
                "title": "Build stuck or taking too long?",
                "summary": "Wait on building status, then retry if failed.",
                "body": """
<ol>
<li>Stay on the building status page and give the job time to finish.</li>
<li>Confirm the app is still installed.</li>
<li>If it fails or never completes, retry from My Stores or AI Store Builder.</li>
<li>Ask BrandBox Coach or Contact Us if it keeps sticking.</li>
</ol>
""",
            },
            {
                "slug": "products-not-showing-in-shopify",
                "title": "Products not showing in Shopify?",
                "summary": "Confirm push succeeded and check Shopify admin.",
                "body": """
<ol>
<li>Verify the product was pushed from <strong>My Imports</strong> (not only imported).</li>
<li>Check Shopify admin → Products.</li>
<li>If push failed, retry after reconnecting the app.</li>
</ol>
""",
            },
            {
                "slug": "cant-log-in",
                "title": "Can't log in?",
                "summary": "Reset password or confirm the signup email.",
                "body": """
<ol>
<li>Confirm you’re using the email from signup/checkout.</li>
<li>Use <strong>Forgot password</strong> on the login page.</li>
<li>If you never set a password, set one via the reset flow.</li>
<li>Still stuck? Contact Us with your account email.</li>
</ol>
""",
            },
            {
                "slug": "payment-issues",
                "title": "Payment issues",
                "summary": "Retry checkout or contact support.",
                "body": """
<ol>
<li>Retry the Checkout / Upgrade flow.</li>
<li>Confirm your card details with your bank if the charge fails.</li>
<li>Contact support with the account email if Pro didn’t activate after payment.</li>
</ol>
""",
            },
        ],
    },
    {
        "slug": "policies",
        "name": "Policies",
        "description": "Privacy, terms, refunds, and data requests.",
        "icon": "gavel",
        "sort_order": 13,
        "articles": [
            {
                "slug": "privacy-policy",
                "title": "Privacy Policy",
                "summary": "Read the full Privacy Policy.",
                "body": """
<p>Our full Privacy Policy is published at <a href="/privacy/">/privacy/</a>.</p>
<p>It covers how BrandBox handles account and product data.</p>
""",
            },
            {
                "slug": "terms-of-service",
                "title": "Terms of Service",
                "summary": "Read the full Terms of Service.",
                "body": """
<p>Our Terms of Service are at <a href="/terms/">/terms/</a>.</p>
""",
            },
            {
                "slug": "refund-policy",
                "title": "Refund Policy",
                "summary": "Read the full Refund Policy.",
                "body": """
<p>Refund eligibility and process are described at <a href="/refund/">/refund/</a>.</p>
""",
            },
            {
                "slug": "data-deletion-gdpr",
                "title": "Data deletion requests (GDPR)",
                "summary": "Request deletion via Contact Us.",
                "body": """
<p>To request account/data deletion:</p>
<ol>
<li>Email or message us via <a href="/contact/">Contact Us</a> from the email on your account.</li>
<li>Include “Data deletion request” in the subject.</li>
<li>We’ll process according to our Privacy Policy and applicable law.</li>
</ol>
""",
            },
        ],
    },
    {
        "slug": "orders-fulfillment",
        "name": "Orders & Fulfillment",
        "description": "Dropshipping orders, shipping times, tracking, and supplier issues.",
        "icon": "local_shipping",
        "sort_order": 14,
        "articles": [
            {
                "slug": "how-dropshipping-fulfillment-works",
                "title": "How order fulfillment works with dropshipping",
                "summary": "Customer pays you; you forward the order to a supplier who ships.",
                "body": """
<p>BrandBox helps you build and stock your Shopify store. Fulfillment stays with you, Shopify, and your suppliers.</p>
<ol>
<li>A customer places an order and pays in your Shopify store.</li>
<li>You (or an automation app) send the order details to your supplier.</li>
<li>The supplier packs and ships to the customer.</li>
<li>You add the tracking number in Shopify so the customer can follow the shipment.</li>
</ol>
<p>Keep supplier processing times honest on your shipping policy page so expectations match reality.</p>
""",
            },
            {
                "slug": "how-long-does-shipping-take",
                "title": "How long does shipping take?",
                "summary": "Publish supplier ranges; don’t promise Amazon-speed delivery.",
                "body": """
<p>Dropshipping times vary by supplier and destination.</p>
<ol>
<li>Ask each supplier for processing time + transit time by region.</li>
<li>Add those ranges to Shopify shipping descriptions and your shipping policy.</li>
<li>Domestic may be days; cross-border can take 1–4+ weeks.</li>
</ol>
<p>Under-promise slightly so “where’s my order” tickets stay manageable.</p>
""",
            },
            {
                "slug": "tracking-numbers-where-customers-find-them",
                "title": "Tracking numbers — where customers find them",
                "summary": "Add tracking in Shopify so customers get the shipping email/portal.",
                "body": """
<ol>
<li>When the supplier shares tracking, open the order in Shopify admin.</li>
<li>Fulfill the order (or add tracking to the fulfillment) with the carrier + number.</li>
<li>Shopify emails the customer; they can also check their order status page / account.</li>
</ol>
<p>If tracking is missing, chase the supplier first, then reply to the customer with an ETA.</p>
""",
            },
            {
                "slug": "customer-asks-wheres-my-order",
                "title": "What to do when a customer asks \"where's my order?\"",
                "summary": "Check Shopify → tracking → supplier, then reply with facts.",
                "body": """
<ol>
<li>Find the order in Shopify and note payment, fulfillment, and tracking status.</li>
<li>If tracking exists, send the link and current carrier status.</li>
<li>If not fulfilled yet, check supplier processing and give a clear ETA.</li>
<li>If past your published window, escalate with the supplier or offer a resolution (refund/reship) per your policy.</li>
</ol>
""",
            },
            {
                "slug": "handling-out-of-stock-supplier-items",
                "title": "Handling out-of-stock supplier items",
                "summary": "Pause selling, notify the customer, swap SKU or refund.",
                "body": """
<ol>
<li>Unpublish or mark the product unavailable in Shopify so new orders stop.</li>
<li>Contact open-order customers quickly with options: wait, swap, or refund.</li>
<li>Ask the supplier for restock ETA; update your listing when stock returns.</li>
<li>In BrandBox, avoid pushing more of that SKU until stock is confirmed.</li>
</ol>
""",
            },
            {
                "slug": "partial-shipments-multi-supplier",
                "title": "Partial shipments (multi-item orders from different suppliers)",
                "summary": "Fulfill each line as it ships; communicate split tracking.",
                "body": """
<ol>
<li>Split the Shopify order mentally by supplier / SKU.</li>
<li>Place each supplier order separately.</li>
<li>Add each tracking number as packages ship (partial fulfillments in Shopify).</li>
<li>Tell the customer items may arrive in more than one package.</li>
</ol>
""",
            },
            {
                "slug": "order-cancellations-before-fulfillment",
                "title": "Order cancellations before fulfillment",
                "summary": "Cancel in Shopify only if the supplier hasn’t shipped.",
                "body": """
<ol>
<li>Check whether you’ve already submitted the order to the supplier.</li>
<li>If not shipped, cancel with the supplier first (if submitted), then cancel/refund in Shopify.</li>
<li>If already shipped, cancellation usually isn’t possible — offer return/refund per policy instead.</li>
</ol>
""",
            },
            {
                "slug": "supplier-ships-wrong-item",
                "title": "What happens if a supplier ships the wrong item?",
                "summary": "Document, contact supplier, make the customer whole.",
                "body": """
<ol>
<li>Ask the customer for photos of what arrived vs. what they ordered.</li>
<li>Open a case with the supplier for reship or credit.</li>
<li>Offer the customer a correct replacement or refund per your store policy — don’t make them wait on the supplier dispute.</li>
<li>Update QC notes so you catch repeat supplier errors.</li>
</ol>
""",
            },
            {
                "slug": "automating-order-fulfillment",
                "title": "Automating order fulfillment",
                "summary": "Use Shopify + supplier apps; BrandBox doesn’t fulfill orders.",
                "body": """
<p>BrandBox focuses on store build and catalog. Fulfillment automation is usually:</p>
<ol>
<li>A supplier/dropship app connected to Shopify, or</li>
<li>CSV / portal uploads you run daily, or</li>
<li>A 3PL once volume justifies it.</li>
</ol>
<p>Whatever you choose, keep tracking synced back into Shopify so customers aren’t left guessing.</p>
""",
            },
        ],
    },
    {
        "slug": "returns-refunds-disputes",
        "name": "Returns, Refunds & Disputes",
        "description": "Store policies, refunds, chargebacks, and claims.",
        "icon": "assignment_return",
        "sort_order": 15,
        "articles": [
            {
                "slug": "setting-up-returns-policy-dropshipping",
                "title": "Setting up a returns policy for a dropshipping store",
                "summary": "Match supplier rules; publish clear windows and who pays return shipping.",
                "body": """
<ol>
<li>Read each supplier’s return rules (many don’t accept returns on all SKUs).</li>
<li>Write a store policy that you can actually honor (window, condition, who pays shipping).</li>
<li>Add it in Shopify: Settings → Policies (and link in footer).</li>
<li>Train your support replies to quote that page, not improvise.</li>
</ol>
""",
            },
            {
                "slug": "handling-customer-refund-requests",
                "title": "Handling customer refund requests",
                "summary": "Verify order status, then refund in Shopify when appropriate.",
                "body": """
<ol>
<li>Confirm order, delivery status, and your published refund rules.</li>
<li>If eligible, issue a full or partial refund from the Shopify order.</li>
<li>If not eligible, explain why and offer alternatives (store credit, exchange) when it still makes sense.</li>
<li>Log supplier-caused issues so you can reclaim cost upstream.</li>
</ol>
""",
            },
            {
                "slug": "what-are-chargebacks",
                "title": "Chargebacks — what they are and how to respond",
                "summary": "Customer disputes a charge with their bank; you must respond with evidence.",
                "body": """
<p>A chargeback is when the customer’s bank pulls back the payment. Shopify/your gateway notifies you.</p>
<ol>
<li>Read the reason code (fraud, not received, not as described, etc.).</li>
<li>Gather evidence before the deadline.</li>
<li>Submit a response through Shopify / your payment provider.</li>
<li>Improve policies and tracking to prevent repeats.</li>
</ol>
""",
            },
            {
                "slug": "disputing-chargeback-with-evidence",
                "title": "Disputing a chargeback with evidence",
                "summary": "Proof of delivery, policy pages, and customer communication win cases.",
                "body": """
<ol>
<li>Export the order, invoices, and refund/policy screenshots.</li>
<li>Add tracking with delivery confirmation when available.</li>
<li>Include chat/email showing you tried to resolve.</li>
<li>Submit before the dispute deadline — late evidence usually loses.</li>
</ol>
""",
            },
            {
                "slug": "item-never-arrived-claims",
                "title": "Handling \"item never arrived\" claims",
                "summary": "Check tracking, then refund/reship per policy.",
                "body": """
<ol>
<li>Verify tracking: in transit, delivered, or stalled.</li>
<li>If delivered, ask the customer to check with neighbors/building; offer next steps per policy.</li>
<li>If lost, open a supplier/carrier claim and refund or reship the customer promptly.</li>
</ol>
""",
            },
            {
                "slug": "item-not-as-described-claims",
                "title": "Handling \"item not as described\" claims",
                "summary": "Compare listing photos/copy to what arrived.",
                "body": """
<ol>
<li>Request photos from the customer.</li>
<li>Compare against your Shopify listing and supplier listing.</li>
<li>If the listing was wrong, fix the listing and refund/replace.</li>
<li>If the supplier sent a bad unit, replace via supplier and keep the customer whole.</li>
</ol>
""",
            },
        ],
    },
    {
        "slug": "customer-service",
        "name": "Customer Service",
        "description": "Support setup, tone, scripts, and resolution choices.",
        "icon": "headset_mic",
        "sort_order": 16,
        "articles": [
            {
                "slug": "setting-up-support-email-contact",
                "title": "Setting up a support email/contact page",
                "summary": "Use a monitored inbox and link it in Shopify.",
                "body": """
<ol>
<li>Create a dedicated support email (e.g. support@yourdomain).</li>
<li>Add it in Shopify customer notifications and your Contact page.</li>
<li>Link Contact in the footer next to policies.</li>
<li>Check the inbox daily — slow replies drive chargebacks.</li>
</ol>
""",
            },
            {
                "slug": "response-time-expectations",
                "title": "Response time expectations customers have",
                "summary": "Aim to reply within 24 hours on business days.",
                "body": """
<p>Most shoppers expect a first reply within about one business day.</p>
<ol>
<li>Publish your support hours on the Contact page.</li>
<li>Send a short acknowledgment if a full answer needs supplier research.</li>
<li>Prioritize “where is my order” and payment issues first.</li>
</ol>
""",
            },
            {
                "slug": "scripts-for-common-questions",
                "title": "Scripts for common customer questions",
                "summary": "Short templates for WISMO, refunds, and damaged items.",
                "body": """
<p><strong>Where’s my order?</strong> “Thanks for reaching out — I checked order #____. Tracking is ____ (link). Current status: ____. Reply if you need anything else.”</p>
<p><strong>Refund request:</strong> “Happy to help. Per our refund policy (link), here’s what I can do: ____. Confirm and I’ll process it.”</p>
<p><strong>Damaged/wrong item:</strong> “Sorry about that — please send a quick photo and I’ll arrange a replacement or refund right away.”</p>
""",
            },
            {
                "slug": "handling-angry-customers",
                "title": "Handling angry or difficult customers",
                "summary": "Stay calm, acknowledge, solve, then prevent.",
                "body": """
<ol>
<li>Acknowledge the frustration without arguing.</li>
<li>Restate the facts (order #, dates, tracking).</li>
<li>Offer a clear fix: refund, reship, or partial credit.</li>
<li>Don’t over-promise supplier timelines you can’t control.</li>
</ol>
""",
            },
            {
                "slug": "refund-vs-replacement",
                "title": "When to offer a refund vs. a replacement",
                "summary": "Replace when stock/time allows; refund when trust is broken or stock is gone.",
                "body": """
<ol>
<li>Offer a <strong>replacement</strong> when stock is available and the customer still wants the product.</li>
<li>Offer a <strong>refund</strong> when the wait is too long, stock is gone, or the customer asks to cancel.</li>
<li>For low-AOV items, a fast refund often costs less than a drawn-out dispute.</li>
</ol>
""",
            },
        ],
    },
    {
        "slug": "payments-taxes",
        "name": "Payments & Taxes",
        "description": "Gateways, tax collection, payouts, and currency.",
        "icon": "account_balance",
        "sort_order": 17,
        "articles": [
            {
                "slug": "connecting-payment-gateway-shopify",
                "title": "Connecting a payment gateway to Shopify",
                "summary": "Enable payments in Shopify Settings → Payments.",
                "body": """
<ol>
<li>In Shopify admin, open <strong>Settings → Payments</strong>.</li>
<li>Activate Shopify Payments (if available) or add a third-party provider.</li>
<li>Complete verification / business details the provider requires.</li>
<li>Place a test order to confirm checkout works.</li>
</ol>
<p>BrandBox does not process your store’s customer payments.</p>
""",
            },
            {
                "slug": "shopify-payments-vs-third-party",
                "title": "Understanding Shopify Payments vs. third-party gateways",
                "summary": "Shopify Payments is native; third parties add extra fees/steps.",
                "body": """
<p><strong>Shopify Payments</strong> is built into checkout where available, with simpler setup and Shopify-managed payouts.</p>
<p><strong>Third-party gateways</strong> (PayPal, etc.) can expand options but may add fees or redirect steps.</p>
<p>Pick based on your country eligibility, fee structure, and which methods your customers expect.</p>
""",
            },
            {
                "slug": "do-i-need-to-charge-sales-tax",
                "title": "Do I need to charge sales tax?",
                "summary": "Depends on your location and nexus — get local advice.",
                "body": """
<p>Tax rules depend on where you (and sometimes your customers) are based.</p>
<ol>
<li>Check whether you have tax obligations in your home region and sales destinations.</li>
<li>When required, enable tax collection in Shopify rather than calculating by hand.</li>
<li>This is not legal advice — confirm with a tax professional for your situation.</li>
</ol>
""",
            },
            {
                "slug": "setting-up-tax-collection-shopify",
                "title": "Setting up tax collection in Shopify",
                "summary": "Configure tax regions in Shopify Settings → Taxes.",
                "body": """
<ol>
<li>Go to Shopify <strong>Settings → Taxes and duties</strong> (wording may vary slightly).</li>
<li>Set regions where you collect tax and review overrides.</li>
<li>Test checkout to see tax line items.</li>
</ol>
""",
            },
            {
                "slug": "payment-payout-schedules",
                "title": "Understanding payment payout schedules",
                "summary": "Gateways hold funds on a rolling schedule, not instantly.",
                "body": """
<p>Card payments usually settle to your bank on a delay (for example a few business days), not the moment an order is placed.</p>
<ol>
<li>Check your payout schedule inside Shopify Payments / your gateway.</li>
<li>Plan supplier payments around that cash timing.</li>
<li>Watch reserves or holds if chargebacks spike.</li>
</ol>
""",
            },
            {
                "slug": "currency-conversion-international",
                "title": "Currency conversion for international sales",
                "summary": "Shopify can show local currencies; conversion fees may apply.",
                "body": """
<ol>
<li>Decide your store currency in Shopify settings.</li>
<li>Enable multi-currency / markets features if you sell internationally.</li>
<li>Expect conversion fees on some cross-border payments.</li>
<li>Price with margin so FX and shipping don’t erase profit.</li>
</ol>
""",
            },
        ],
    },
    {
        "slug": "shipping-setup",
        "name": "Shipping Setup",
        "description": "Rates, zones, free shipping, insurance, and duties.",
        "icon": "map",
        "sort_order": 18,
        "articles": [
            {
                "slug": "setting-shipping-rates-and-zones",
                "title": "Setting shipping rates and zones",
                "summary": "Configure profiles and zones in Shopify Shipping settings.",
                "body": """
<ol>
<li>Open Shopify <strong>Settings → Shipping and delivery</strong>.</li>
<li>Create zones (domestic, EU, rest of world, etc.).</li>
<li>Add rates that match supplier reality (price + time).</li>
<li>Re-test checkout from a sample address in each zone.</li>
</ol>
""",
            },
            {
                "slug": "free-vs-flat-vs-calculated-shipping",
                "title": "Free shipping vs. flat rate vs. calculated",
                "summary": "Pick a model you can sustain on dropship margins.",
                "body": """
<p><strong>Free shipping</strong> — bake cost into product price; converts well but needs margin.</p>
<p><strong>Flat rate</strong> — simple for customers; easy to explain in ads.</p>
<p><strong>Calculated</strong> — more accurate, more setup; watch for sticker shock at checkout.</p>
""",
            },
            {
                "slug": "international-shipping-considerations",
                "title": "International shipping considerations",
                "summary": "Times, duties, restricted countries, and returns complexity.",
                "body": """
<ol>
<li>Confirm your supplier ships to the countries you sell.</li>
<li>Show longer delivery windows for international orders.</li>
<li>Decide who pays duties (DDP vs DDU) and say so in policy.</li>
<li>Expect harder returns across borders — price risk into policy.</li>
</ol>
""",
            },
            {
                "slug": "shipping-insurance",
                "title": "Shipping insurance",
                "summary": "Optional protection for high-AOV or loss-prone lanes.",
                "body": """
<p>Some carriers/suppliers offer insurance for lost or damaged parcels.</p>
<ol>
<li>Use it on higher-value SKUs where replacement cost hurts.</li>
<li>Keep invoices and tracking for claims.</li>
<li>Don’t promise customers insurance coverage you didn’t buy.</li>
</ol>
""",
            },
            {
                "slug": "customs-import-duties",
                "title": "What to do about customs/import duties?",
                "summary": "Disclose possible duties; choose DDP if you want fewer surprises.",
                "body": """
<ol>
<li>State in your shipping policy that international orders may incur duties/taxes.</li>
<li>If using DDP, include duty cost in pricing/shipping.</li>
<li>If DDU, warn customers they may pay on delivery.</li>
<li>Unclear duty messaging is a common chargeback trigger.</li>
</ol>
""",
            },
        ],
    },
    {
        "slug": "marketing-traffic",
        "name": "Marketing & Traffic",
        "description": "Ads, email, SEO, and outreach basics for new stores.",
        "icon": "campaign",
        "sort_order": 19,
        "articles": [
            {
                "slug": "first-facebook-instagram-ad",
                "title": "Running your first Facebook/Instagram ad",
                "summary": "BrandBox doesn’t create ads — here’s a safe first setup outline.",
                "body": """
<p>BrandBox does not generate ads. For a first Meta campaign:</p>
<ol>
<li>Install the Meta Pixel on Shopify.</li>
<li>Create a simple conversion campaign to your product page.</li>
<li>Start with a small daily budget and one clear creative + offer.</li>
<li>Kill ads that don’t get add-to-carts after enough spend; iterate creatives.</li>
</ol>
""",
            },
            {
                "slug": "first-tiktok-ad",
                "title": "Running your first TikTok ad",
                "summary": "Native-looking creative usually beats polished brand videos.",
                "body": """
<ol>
<li>Set up TikTok Ads and connect your Shopify catalog/pixel tools as required.</li>
<li>Use short UGC-style video showing the product in use.</li>
<li>Send traffic to a fast mobile product page.</li>
<li>Start small, watch CPA, and pause losers quickly.</li>
</ol>
""",
            },
            {
                "slug": "ad-budget-basics",
                "title": "Understanding ad budget basics",
                "summary": "Budget for learning, then scale only what profits.",
                "body": """
<ol>
<li>Know your product margin after product + shipping + fees.</li>
<li>Set a test budget you’re willing to lose while learning.</li>
<li>Track cost per purchase vs. profit per order.</li>
<li>Scale only when purchases are profitable after returns/chargebacks.</li>
</ol>
""",
            },
            {
                "slug": "email-marketing-basics",
                "title": "Email marketing basics for a new store",
                "summary": "Welcome, shipping, and abandoned-cart flows first.",
                "body": """
<ol>
<li>Connect an email app (Klaviyo, Shopify Email, etc.).</li>
<li>Start with welcome + order/shipping notifications (Shopify handles transactional).</li>
<li>Add a simple abandoned checkout flow.</li>
<li>Keep compliance: consent and unsubscribe links.</li>
</ol>
""",
            },
            {
                "slug": "abandoned-cart-recovery",
                "title": "Abandoned cart recovery",
                "summary": "Remind shoppers who almost bought.",
                "body": """
<ol>
<li>Enable Shopify abandoned checkout emails or an ESP flow.</li>
<li>Send 1–3 reminders with the product and a clear checkout link.</li>
<li>Don’t over-discount on email one — try value first.</li>
</ol>
""",
            },
            {
                "slug": "basic-seo-new-shopify-store",
                "title": "Basic SEO for a new Shopify store",
                "summary": "Titles, descriptions, speed, and indexable pages.",
                "body": """
<ol>
<li>Write unique product titles and meta descriptions.</li>
<li>Use clean URLs and descriptive alt text on images.</li>
<li>Submit your sitemap in Google Search Console.</li>
<li>Don’t expect SEO alone to launch a brand-new dropship store overnight — pair with ads/content.</li>
</ol>
""",
            },
            {
                "slug": "influencer-affiliate-outreach-basics",
                "title": "Influencer/affiliate outreach basics",
                "summary": "Start small; track codes; BrandBox also has its own affiliate program.",
                "body": """
<ol>
<li>Offer a unique discount code or commission per creator.</li>
<li>Send product info + creative angles, not just “promote my store.”</li>
<li>Track which codes actually sell.</li>
<li>Separately, creators can apply to the BrandBox affiliate program via <a href="/affiliate/">/affiliate/</a>.</li>
</ol>
""",
            },
        ],
    },
    {
        "slug": "analytics-growth",
        "name": "Analytics & Growth",
        "description": "Shopify metrics, CAC, scaling, and killing losers.",
        "icon": "monitoring",
        "sort_order": 20,
        "articles": [
            {
                "slug": "reading-shopify-analytics",
                "title": "Reading your Shopify analytics dashboard",
                "summary": "Start with sales, conversion, and top products.",
                "body": """
<ol>
<li>Open Shopify <strong>Analytics</strong> (or Home metrics).</li>
<li>Check sessions, conversion rate, and total sales for the period.</li>
<li>Identify top products and traffic sources.</li>
<li>Use BrandBox Overview for build/readiness — use Shopify for store commerce metrics.</li>
</ol>
""",
            },
            {
                "slug": "understanding-conversion-rate",
                "title": "Understanding conversion rate",
                "summary": "Purchases ÷ sessions — improve offer, page, and trust.",
                "body": """
<p>Conversion rate is roughly orders divided by sessions.</p>
<ol>
<li>If traffic is high but conversion is low, fix product page, price, shipping clarity, or trust (policies/reviews).</li>
<li>If conversion is fine but sales are low, you need more qualified traffic.</li>
</ol>
""",
            },
            {
                "slug": "understanding-cac",
                "title": "Understanding customer acquisition cost",
                "summary": "Ad spend ÷ new customers — must stay under profit per order.",
                "body": """
<ol>
<li>Sum ad spend for a period.</li>
<li>Divide by new paying customers from those ads.</li>
<li>Compare CAC to profit after product, shipping, and fees.</li>
<li>If CAC &gt; profit, pause and fix offer/creative before scaling.</li>
</ol>
""",
            },
            {
                "slug": "when-to-scale-ad-spend",
                "title": "When to scale ad spend",
                "summary": "Scale only after stable profitable delivery.",
                "body": """
<ol>
<li>Confirm profitable purchases across several days, not one lucky day.</li>
<li>Increase budget gradually (not huge jumps that break learning).</li>
<li>Watch CAC, refund rate, and stock/supplier capacity as you grow.</li>
</ol>
""",
            },
            {
                "slug": "when-product-isnt-working",
                "title": "When a product isn't working — how to know?",
                "summary": "Weak CTR, weak conversion, or unprofitable CAC.",
                "body": """
<ol>
<li>Ads get impressions but almost no clicks → creative/offer problem.</li>
<li>Clicks but no add-to-carts → landing page/price/trust problem.</li>
<li>Add-to-carts but no purchases → shipping cost, checkout friction, or payment issues.</li>
<li>Purchases but no profit → cut spend, raise price, or retire the SKU.</li>
</ol>
""",
            },
        ],
    },
    {
        "slug": "store-legal-policies",
        "name": "Legal & Store Policies",
        "description": "Policies for your Shopify store (not BrandBox’s policies).",
        "icon": "policy",
        "sort_order": 21,
        "articles": [
            {
                "slug": "do-i-need-store-privacy-policy",
                "title": "Do I need a privacy policy?",
                "summary": "Yes for most online stores collecting customer data.",
                "body": """
<p>If you collect emails, addresses, or payment data, you generally need a privacy policy on your store.</p>
<ol>
<li>Add one under Shopify Settings → Policies.</li>
<li>Link it in the footer and checkout where required.</li>
<li>BrandBox’s own privacy page (<a href="/privacy/">/privacy/</a>) covers BrandBox — your store needs its own.</li>
</ol>
""",
            },
            {
                "slug": "do-i-need-store-terms",
                "title": "Do I need terms of service?",
                "summary": "Recommended for rules on use, orders, and liability.",
                "body": """
<p>Store Terms of Service set expectations for purchases, accounts, and acceptable use.</p>
<ol>
<li>Publish Terms in Shopify policies.</li>
<li>Keep them consistent with refund/shipping pages.</li>
<li>BrandBox Terms (<a href="/terms/">/terms/</a>) are separate from your store’s terms.</li>
</ol>
""",
            },
            {
                "slug": "business-license-to-dropship",
                "title": "Do I need a business license to dropship?",
                "summary": "Often yes depending on your city/country — verify locally.",
                "body": """
<p>Many places require a business registration or license to sell online — rules vary widely.</p>
<p>Check your local requirements (and tax IDs) before scaling ads. This isn’t legal advice.</p>
""",
            },
            {
                "slug": "age-restrictions-restricted-categories",
                "title": "Age restrictions / restricted product categories",
                "summary": "Some niches are banned or restricted by Shopify, ads, or law.",
                "body": """
<ol>
<li>Review Shopify’s Acceptable Use / restricted products list.</li>
<li>Check ad platform rules (Meta/TikTok ban many categories).</li>
<li>Avoid medical claims and regulated goods unless you’re properly licensed.</li>
<li>If unsure, pick another niche in AI Store Builder rather than risk shutdowns.</li>
</ol>
""",
            },
            {
                "slug": "gdpr-basics-eu-customers",
                "title": "GDPR basics if selling to EU customers",
                "summary": "Be transparent, minimize data, honor access/deletion asks.",
                "body": """
<ol>
<li>Publish a clear privacy policy and cookie/consent approach where required.</li>
<li>Only collect data you need to fulfill orders.</li>
<li>Respond to access/deletion requests in a timely way.</li>
<li>Use Shopify tools and your ESP’s compliance features — get counsel for complex cases.</li>
</ol>
""",
            },
        ],
    },
    {
        "slug": "supplier-product-management",
        "name": "Supplier & Product Management",
        "description": "Stock, supplier switches, QC, listings, and out-of-stock ops.",
        "icon": "inventory",
        "sort_order": 22,
        "articles": [
            {
                "slug": "supplier-out-of-stock-long-term",
                "title": "What to do if a supplier goes out of stock long-term?",
                "summary": "Unpublish, refund open risk, find a replacement supplier.",
                "body": """
<ol>
<li>Unpublish the product in Shopify immediately.</li>
<li>Resolve any open orders (refund/alternative).</li>
<li>Search for a replacement supplier with samples if needed.</li>
<li>Update BrandBox imports/listings only after the new source is reliable.</li>
</ol>
""",
            },
            {
                "slug": "switching-suppliers-for-a-product",
                "title": "Switching suppliers for a product",
                "summary": "Match quality and shipping before you flip live traffic.",
                "body": """
<ol>
<li>Order a sample from the new supplier.</li>
<li>Compare price, shipping time, and packaging to your listing promises.</li>
<li>Update cost/shipping settings so margins stay real.</li>
<li>Switch fulfillment instructions, then monitor the first orders closely.</li>
</ol>
""",
            },
            {
                "slug": "quality-control-bad-batches",
                "title": "Quality control — handling bad product batches",
                "summary": "Stop sales, notify customers, reclaim from supplier.",
                "body": """
<ol>
<li>Pause ads and unpublish if defects are widespread.</li>
<li>Refund or replace affected customers quickly.</li>
<li>Send evidence to the supplier for credit.</li>
<li>Don’t restock the same batch blindly — re-sample first.</li>
</ol>
""",
            },
            {
                "slug": "communicating-with-suppliers",
                "title": "Communicating with suppliers directly",
                "summary": "Be specific: SKU, order ID, photos, and asked outcome.",
                "body": """
<ol>
<li>Use clear subject lines with your order/SKU IDs.</li>
<li>Attach photos for quality or wrong-item issues.</li>
<li>Ask for one outcome: reship, refund, or stock ETA.</li>
<li>Keep a simple log — it helps chargeback evidence later.</li>
</ol>
""",
            },
            {
                "slug": "connect-supplier-manage-listings",
                "title": "Connecting suppliers and managing product listings",
                "summary": "List in BrandBox/Shopify; fulfill via supplier tools.",
                "body": """
<ol>
<li>Import winning products in BrandBox (<strong>Product Hunter</strong> → <strong>My Imports</strong>) and push to Shopify.</li>
<li>Connect your fulfillment/supplier app or portal to those SKUs.</li>
<li>Keep title, price, and shipping text aligned with what the supplier can deliver.</li>
<li>When stock changes, update Shopify inventory/status so you don’t oversell.</li>
</ol>
""",
            },
            {
                "slug": "solving-out-of-stock-on-listings",
                "title": "Solving out-of-stock on live listings",
                "summary": "Sync inventory, hide SKUs, and restore only when confirmed.",
                "body": """
<ol>
<li>Set inventory to 0 or unpublish when the supplier is dry.</li>
<li>Turn off ads pointing at that URL.</li>
<li>Message waiting customers with options.</li>
<li>When restocked, update inventory, re-enable the listing, then resume traffic.</li>
</ol>
""",
            },
            {
                "slug": "mapping-skus-across-systems",
                "title": "Keeping SKUs mapped across Shopify and suppliers",
                "summary": "One SKU map prevents wrong-item shipments.",
                "body": """
<ol>
<li>Use a consistent SKU on the Shopify variant and the supplier product ID.</li>
<li>When you push from BrandBox imports, note the Shopify product/variant IDs.</li>
<li>In your fulfillment tool, map those IDs to the supplier SKU.</li>
<li>Re-check mapping after any supplier switch.</li>
</ol>
""",
            },
            {
                "slug": "link-existing-products-to-supplier",
                "title": "Linking existing store products to a supplier",
                "summary": "Map products you already sell to a supplier so fulfillment, tracking, and stock can sync.",
                "body": """
<p>If your Shopify store already has many products but you’re not sure which supplier each one comes from, you need a <strong>product ↔ supplier link</strong> before auto-fulfillment, tracking, or stock sync can work.</p>
<p>BrandBox helps you <em>add</em> catalog via Product Hunter → My Imports → push. Linking fulfillment for products already live is done in Shopify + your supplier/fulfillment app.</p>

<p><strong>1. Build a product map (spreadsheet is fine)</strong></p>
<ol>
<li>Export products from Shopify (title, variant SKU, barcode, price, inventory).</li>
<li>For each SKU, note the supplier name, supplier product ID/URL, cost, and shipping time.</li>
<li>If you don’t know the supplier, reverse-search photos/titles, check old invoices/emails, or order a sample from candidate suppliers until packaging and quality match.</li>
</ol>

<p><strong>2. Put a stable ID on every variant</strong></p>
<ol>
<li>In Shopify, open each product variant and set a clear <strong>SKU</strong> (and barcode if you use one).</li>
<li>Use the same SKU (or a documented mapping) in the supplier’s catalog.</li>
<li>Avoid blank or duplicate SKUs — automation can’t route orders without a unique key.</li>
</ol>

<p><strong>3. Connect a fulfillment / dropship app</strong></p>
<ol>
<li>Install your supplier’s official app or a multi-supplier fulfillment tool on the Shopify store.</li>
<li>In that app, use <strong>Link product</strong> / <strong>Map product</strong> / <strong>Connect listing</strong> (wording varies).</li>
<li>Match each Shopify variant to the supplier’s product/variant ID.</li>
<li>Save the link, then place a low-risk test order to confirm the right item is ordered.</li>
</ol>

<p><strong>4. What the link unlocks</strong></p>
<ol>
<li><strong>Auto fulfillment</strong> — new paid orders can be sent to the supplier without manual copy-paste.</li>
<li><strong>Tracking</strong> — when the supplier ships, tracking can sync back into the Shopify order.</li>
<li><strong>Stock / OOS</strong> — inventory updates can unpublish or zero-out SKUs when the supplier runs dry.</li>
<li><strong>Stats</strong> — cost, margin, and fulfillment success become measurable per linked SKU.</li>
</ol>

<p><strong>5. If a product has no supplier yet</strong></p>
<ol>
<li>Don’t enable auto-fulfill for that SKU.</li>
<li>Either find and link a supplier, or unpublish until you can fulfill reliably.</li>
<li>For new catalog, prefer BrandBox imports so you start with known winning products, then map fulfillment the same way.</li>
</ol>

<p><strong>Quick checklist</strong></p>
<ol>
<li>Every live variant has a unique SKU.</li>
<li>Each SKU has a documented supplier + supplier product ID.</li>
<li>Fulfillment app shows “linked” / mapped status.</li>
<li>Test order → correct item → tracking appears in Shopify.</li>
</ol>
""",
            },
        ],
    },
]
