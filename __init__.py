# prevent ImportErrors when nose initialises
import pagefeed.console as console
console.add_gae_paths()
