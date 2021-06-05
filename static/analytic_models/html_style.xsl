<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:output
method="html"/>

<xsl:template match="/analytic_model">
  
  <xsl:value-of select="name"/>
  
   <xsl:apply-templates select="concepts"/>

</xsl:template>


<xsl:template match="concepts">
    <ul>
   <xsl:apply-templates select="concept"/>
   </ul>
</xsl:template>


<xsl:template match="concept">
   <li>
   <b><xsl:value-of select="name"/></b>: <xsl:value-of select="description"/>
      <xsl:apply-templates select="concepts"/>
   </li>
</xsl:template>

</xsl:stylesheet>