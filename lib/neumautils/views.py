from django.views.generic import TemplateView, FormView
from manager.models import Corpus, Opus, Bookmark

from django.core.files import File
from django.conf import settings

from django.urls  import reverse

from neumasearch.SearchContext import SearchContext

class NeumaView(TemplateView):
	'''Override the view class to always add the list of t
	top-level corpora to the context '''


	def top_level_stats(self):

		return {"total_corpus": Corpus.objects.all().count(),
				"total_opus" : Opus.objects.all().count()}

	def top_level_corpora(self):
		
		# Check that the Root corpus does exist
		try:
			root = Corpus.objects.get(ref=settings.NEUMA_ROOT_CORPUS_REF)
		except Corpus.DoesNotExist:
			# Create the root corpus
			root = Corpus(ref=settings.NEUMA_ROOT_CORPUS_REF)
			root.title = "Collections - Neuma"
			root.short_title = "All"
			root.short_description = "All collections"
			root.is_public = True
			root.save()
   
			with open("static/images/all-cover.jpg", "rb") as f2:
				root.cover.save ("cover.jpg", File(f2))
				
		# Update current root corpora
		corpora  = Corpus.objects.filter(parent__isnull=True)
		for corpus in corpora:
			if corpus.ref != root.ref:
				corpus.parent = root
				corpus.save()
				
		# Create the list of corpora visible by the user
		corpora  = Corpus.objects.filter(parent=root).order_by("ref")
		visible_corpora = []
		for corpus in corpora:
			# We do not show these corpora in the top-level list 
			if  corpus.ref == settings.NEUMA_EXTERNAL_CORPUS_REF:
			   continue

		   
			if corpus.is_public: 
				visible_corpora.append(corpus)
			else:
				if self.request.user != None:
					## Check user right
					if self.request.user.has_perm('view_corpus', corpus):
						visible_corpora.append(corpus)

		return visible_corpora

	def recent_bookmarks(self):
		bkms =   Bookmark.objects.order_by('opus').values('opus').distinct()[:5]
		opera = []
		for oid in bkms:
			opera.append (Opus.objects.get(id=oid['opus']))

		return opera

	def get_context_for_layout(self):
		"""
		   Create HTML code to display the context (breadcrumb) in the Layout
		"""
		# Now build the HTML code. Dirty, but who cares?
		if self.search_context.is_opus():
			opus = Opus.objects.get(ref=self.search_context.ref)
			if len(opus.title) < 15:
				label = opus.title
			else:
				label = opus.local_ref()
			context = "<li class='selected'><a href='" + opus.get_url() + "'>" + label+ "</a> </li>"
			corpus_ref = opus.corpus.ref
		else:
			context = ""
			corpus_ref = self.search_context.ref

		while corpus_ref != "":
				corpus = Corpus.objects.get(ref=corpus_ref)
				context = ("<li class='selected'>"+ "<a href='" + corpus.get_url() + "'>" + corpus.short_title+ "</a> </li><ul>" + context + "</ul>")
				corpus_ref = Corpus.parent_ref(corpus_ref)

		return context

	def get_context_data(self, **kwargs):
		# Used to make sure that the search/navigation context is initialized

		# Create a default search context if it does not exist
		if "search_context" not in self.request.session:
			self.search_context = SearchContext()
			self.request.session["search_context"] = self.search_context.toJSON()
		else:
			self.search_context = SearchContext.fromJSON(self.request.session["search_context"])
			print (f"After decoding search context: {self.search_context} ") 
		# Add some useful constant (we could use a context processor - maybe)
		context = super(NeumaView, self).get_context_data(**kwargs)
		context['NEUMA_URL'] = settings.NEUMA_URL
		context["page_title"] = "Neuma Digital Library -- V3"
		return context

