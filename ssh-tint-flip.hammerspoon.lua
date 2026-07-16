-- Fire ssh-tint-flip on every macOS light/dark appearance change, event-driven
-- (no polling). Pair with `SSH_TINT_POLL=0` in the ssh/mosh wrapper to rely
-- purely on this hook.
--
-- Install: copy this file next to your Hammerspoon config and load it from
-- ~/.hammerspoon/init.lua with:
--     dofile(os.getenv("HOME") .. "/bin/ssh-tint-flip.hammerspoon.lua")
-- then reload Hammerspoon.

sshTintWatcher = hs.distributednotifications.new(function()
    -- ~/bin may not be on Hammerspoon's PATH; call the absolute path.
    hs.execute(os.getenv("HOME") .. "/bin/ssh-tint-flip", false)
end, "AppleInterfaceThemeChangedNotification")

sshTintWatcher:start()
